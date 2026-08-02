from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_mail import Mail, Message
import hashlib
import os
import jwt
import sqlite3
import secrets
import re
from datetime import datetime, timedelta, timezone
from functools import wraps

app = Flask(__name__)
app.secret_key = os.urandom(24)

# ── Email Configuration ──────────────────────────────────────────────
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'johncarlolanggoy@gmail.com'  # Palitan ng iyong email
app.config['MAIL_PASSWORD'] = 'jums suya ovmz trdw'     # Palitan ng iyong app password
app.config['MAIL_DEFAULT_SENDER'] = 'johncarlolanggoy@gmail.com'

mail = Mail(app)

# ── JWT Configuration ────────────────────────────────────────────────
JWT_SECRET = "your-super-secret-jwt-key-change-in-production"
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_HOURS = 1

# ── Login Attempt Limiter Config ─────────────────────────────────────
MAX_ATTEMPTS = 5
LOCKOUT_MINUTES = 15

# ── Database Setup ────────────────────────────────────────────────────
DB_FILE = "secure_auth.db"

def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize SQLite database with all required tables."""
    conn = get_db()
    c = conn.cursor()

    # Check if users table exists
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
    table_exists = c.fetchone()
    
    if table_exists:
        # Check if email column exists
        c.execute("PRAGMA table_info(users)")
        columns = [col[1] for col in c.fetchall()]
        
        if 'email' not in columns:
            print("Migrating database...")
            c.execute("ALTER TABLE users RENAME TO users_old")
            c.execute("""
                CREATE TABLE users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT UNIQUE NOT NULL,
                    salt TEXT NOT NULL,
                    hashed_password TEXT NOT NULL,
                    role TEXT NOT NULL DEFAULT 'user',
                    phone TEXT,
                    address TEXT,
                    created_at TEXT NOT NULL
                )
            """)
            c.execute("""
                INSERT INTO users (id, email, salt, hashed_password, role, created_at)
                SELECT id, username, salt, hashed_password, role, created_at 
                FROM users_old
            """)
            c.execute("DROP TABLE users_old")
            print("Migration completed!")
    else:
        c.execute("""
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                salt TEXT NOT NULL,
                hashed_password TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'user',
                phone TEXT,
                address TEXT,
                created_at TEXT NOT NULL
            )
        """)

    # ── Pets table with image column and pet_type ──────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS pets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_email TEXT NOT NULL,
            pet_type TEXT DEFAULT 'Dog',
            name TEXT NOT NULL,
            breed TEXT,
            age INTEGER,
            gender TEXT,
            color TEXT,
            weight REAL,
            medical_history TEXT,
            allergies TEXT,
            pet_image TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (customer_email) REFERENCES users(email) ON DELETE CASCADE
        )
    """)

    # ── Vaccinations table ──────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS vaccinations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pet_id INTEGER NOT NULL,
            vaccine_name TEXT NOT NULL,
            date_given TEXT NOT NULL,
            next_due_date TEXT,
            notes TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (pet_id) REFERENCES pets(id) ON DELETE CASCADE
        )
    """)

    # ── Visits table ────────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS visits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pet_id INTEGER NOT NULL,
            visit_date TEXT NOT NULL,
            reason TEXT,
            diagnosis TEXT,
            treatment TEXT,
            notes TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (pet_id) REFERENCES pets(id) ON DELETE CASCADE
        )
    """)

    # ── Medical Records table (for Veterinarian) ──────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS medical_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pet_id INTEGER NOT NULL,
            vet_email TEXT NOT NULL,
            visit_date TEXT NOT NULL,
            diagnosis TEXT NOT NULL,
            treatment TEXT,
            prescription TEXT,
            notes TEXT,
            status TEXT DEFAULT 'active',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (pet_id) REFERENCES pets(id) ON DELETE CASCADE,
            FOREIGN KEY (vet_email) REFERENCES users(email) ON DELETE CASCADE
        )
    """)

    # ── ML Recommendations table ──────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS ml_recommendations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pet_id INTEGER NOT NULL,
            recommendation_type TEXT NOT NULL,
            recommendation_text TEXT NOT NULL,
            confidence_score REAL,
            status TEXT DEFAULT 'pending',
            vet_notes TEXT,
            validated_at TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (pet_id) REFERENCES pets(id) ON DELETE CASCADE
        )
    """)

    # ── Appointments table ────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_email TEXT NOT NULL,
            pet_id INTEGER NOT NULL,
            service_type TEXT NOT NULL,
            appointment_date TEXT NOT NULL,
            appointment_time TEXT NOT NULL,
            notes TEXT,
            status TEXT DEFAULT 'pending',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (customer_email) REFERENCES users(email) ON DELETE CASCADE,
            FOREIGN KEY (pet_id) REFERENCES pets(id) ON DELETE CASCADE
        )
    """)

    # ── Services table ──────────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS services (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            price REAL,
            duration INTEGER,
            is_active INTEGER DEFAULT 1,
            created_at TEXT NOT NULL
        )
    """)

    # ── Add default services ────────────────────────────────────────────
    c.execute("SELECT id FROM services LIMIT 1")
    if not c.fetchone():
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        default_services = [
            ("Full Grooming", "Complete grooming service including bath, haircut, nail trim, and ear cleaning", 65.00, 90, 1, now),
            ("Bath & Brush", "Basic bath and brush service", 35.00, 45, 1, now),
            ("Nail Trim", "Professional nail trimming service", 15.00, 20, 1, now),
            ("Teeth Cleaning", "Dental cleaning for your pet", 25.00, 30, 1, now),
            ("De-shedding", "Remove loose fur to reduce shedding", 50.00, 60, 1, now),
            ("Creative Styling", "Creative grooming and styling", 85.00, 120, 1, now),
            ("Ear Cleaning", "Professional ear cleaning", 20.00, 20, 1, now),
            ("Vaccination", "Pet vaccination service", 40.00, 30, 1, now),
            ("Health Check-up", "Complete health examination", 50.00, 45, 1, now),
        ]
        for service in default_services:
            c.execute("""
                INSERT INTO services (name, description, price, duration, is_active, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, service)

    # Login attempts table
    c.execute("""
        CREATE TABLE IF NOT EXISTS login_attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            attempt_time TEXT NOT NULL,
            success INTEGER NOT NULL DEFAULT 0
        )
    """)

    # Password reset tokens table
    c.execute("""
        CREATE TABLE IF NOT EXISTS reset_tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            token TEXT UNIQUE NOT NULL,
            expires_at TEXT NOT NULL,
            used INTEGER NOT NULL DEFAULT 0
        )
    """)

    # Ensure a default admin account exists
    c.execute("SELECT id FROM users WHERE email='admin@petlink.com'")
    if not c.fetchone():
        salt = generate_salt()
        c.execute(
            "INSERT INTO users (email, salt, hashed_password, role, phone, address, created_at) VALUES (?,?,?,?,?,?,?)",
            ("admin@petlink.com", salt, hash_password("Admin@1234", salt), "admin", 
             "09171234567", "48 B. Serrano St., Caloocan City",
             datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )

    conn.commit()
    conn.close()

# ── Crypto Helpers ────────────────────────────────────────────────────
def generate_salt():
    return os.urandom(32).hex()

def hash_password(password, salt):
    return hashlib.sha256((password + salt).encode()).hexdigest()

def is_strong_password(password):
    if len(password) < 8:
        return False, 'Password must be at least 8 characters.'
    if not re.search(r'[A-Z]', password):
        return False, 'Password must contain at least one uppercase letter.'
    if not re.search(r'[a-z]', password):
        return False, 'Password must contain at least one lowercase letter.'
    if not re.search(r'[0-9]', password):
        return False, 'Password must contain at least one number.'
    if not re.search(r'[^A-Za-z0-9]', password):
        return False, 'Password must contain at least one special character.'
    return True, ''

def is_valid_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def is_valid_phone(phone):
    if not phone:
        return True
    phone = re.sub(r'[\s\-\(\)]', '', phone)
    if re.match(r'^(09|\+639|9)\d{9}$', phone):
        return True
    if re.match(r'^[0-9]{2,8}$', phone):
        return True
    return False

# ── Login Attempt Limiter ─────────────────────────────────────────────
def record_attempt(email, success):
    conn = get_db()
    conn.execute(
        "INSERT INTO login_attempts (email, attempt_time, success) VALUES (?,?,?)",
        (email, datetime.now(timezone.utc).isoformat(), int(success))
    )
    conn.commit()
    conn.close()

def get_lockout_status(email):
    conn = get_db()
    window_start = (datetime.now(timezone.utc) - timedelta(minutes=LOCKOUT_MINUTES)).isoformat()

    row = conn.execute(
        "SELECT COUNT(*) as cnt FROM login_attempts WHERE email=? AND attempt_time>? AND success=0",
        (email, window_start)
    ).fetchone()
    failed_count = row["cnt"]

    remaining = 0
    is_locked = False
    if failed_count >= MAX_ATTEMPTS:
        nth = conn.execute(
            "SELECT attempt_time FROM login_attempts WHERE email=? AND attempt_time>? AND success=0 "
            "ORDER BY attempt_time ASC LIMIT 1 OFFSET ?",
            (email, window_start, MAX_ATTEMPTS - 1)
        ).fetchone()
        if nth:
            lock_start = datetime.fromisoformat(nth["attempt_time"])
            unlock_at = lock_start + timedelta(minutes=LOCKOUT_MINUTES)
            now = datetime.now(timezone.utc)
            if now < unlock_at:
                is_locked = True
                remaining = int((unlock_at - now).total_seconds())

    conn.close()
    return is_locked, remaining, failed_count

# ── JWT Authentication ────────────────────────────────────────────────
def generate_jwt(email, role):
    payload = {
        "sub": email,
        "role": role,
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRY_HOURS)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def verify_jwt(token):
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def jwt_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = session.get("jwt_token")
        if not token:
            return redirect(url_for("login"))
        payload = verify_jwt(token)
        if not payload:
            session.clear()
            return redirect(url_for("login"))
        request.current_user = payload
        return f(*args, **kwargs)
    return decorated

# ── Role-Based Access Control ────────────────────────────────────────
def role_required(*roles):
    def decorator(f):
        @wraps(f)
        @jwt_required
        def decorated(*args, **kwargs):
            if request.current_user.get("role") not in roles:
                return jsonify({"success": False, "message": "Access denied: insufficient permissions."}), 403
            return f(*args, **kwargs)
        return decorated
    return decorator

# ── Email Helper Function ─────────────────────────────────────────────
def send_email_notification(recipient, subject, body, appointment_data=None):
    """
    Send email notification for appointment updates with HTML formatting.
    Returns True if email was sent successfully, False otherwise.
    """
    try:
        msg = Message(subject, recipients=[recipient])
        
        # Create HTML email body
        status_colors = {
            'pending': '#f59e0b',
            'confirmed': '#10b981',
            'completed': '#38bdf8',
            'cancelled': '#ef4444'
        }
        status_color = status_colors.get(appointment_data.get('status', 'pending') if appointment_data else 'pending', '#94a3b8')
        
        html_body = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; background-color: #0f172a; color: #e2e8f0; margin: 0; padding: 20px; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 30px; background: #1e293b; border-radius: 16px; border: 1px solid #334155; }}
                .header {{ text-align: center; border-bottom: 1px solid #334155; padding-bottom: 20px; }}
                .header h1 {{ color: #38bdf8; font-size: 28px; margin: 0; }}
                .header .subtitle {{ color: #94a3b8; font-size: 14px; }}
                .content {{ padding: 20px 0; }}
                .content h2 {{ color: #38bdf8; font-size: 22px; margin-bottom: 10px; }}
                .content p {{ color: #94a3b8; line-height: 1.6; }}
                .details {{ background: #0f172a; border-radius: 12px; padding: 20px; border: 1px solid #334155; margin-top: 20px; }}
                .detail {{ padding: 8px 0; border-bottom: 1px solid #1e293b; }}
                .detail:last-child {{ border-bottom: none; }}
                .detail strong {{ color: #38bdf8; }}
                .status-badge {{ display: inline-block; padding: 4px 16px; border-radius: 20px; font-weight: 600; font-size: 14px; background: {status_color}; color: #0f172a; }}
                .footer {{ text-align: center; border-top: 1px solid #334155; padding-top: 20px; color: #64748b; font-size: 12px; }}
                .footer .address {{ color: #94a3b8; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🐾 PetLink</h1>
                    <div class="subtitle">Canine Distemper Center</div>
                </div>
                <div class="content">
                    <h2>{subject}</h2>
                    <p>{body}</p>
        """
        
        if appointment_data:
            status_label = appointment_data.get('status', 'pending').upper()
            html_body += f"""
                    <div class="details">
                        <h3 style="color: #38bdf8; margin-top: 0; margin-bottom: 15px;">📋 Appointment Details</h3>
                        <div class="detail"><strong>🐕 Pet:</strong> {appointment_data.get('pet_name', 'N/A')}</div>
                        <div class="detail"><strong>✂️ Service:</strong> {appointment_data.get('service', 'N/A')}</div>
                        <div class="detail"><strong>📅 Date:</strong> {appointment_data.get('date', 'N/A')}</div>
                        <div class="detail"><strong>⏰ Time:</strong> {appointment_data.get('time', 'N/A')}</div>
                        <div class="detail"><strong>📌 Status:</strong> <span class="status-badge">{status_label}</span></div>
                        {f'<div class="detail"><strong>📝 Notes:</strong> {appointment_data.get("notes", "")}</div>' if appointment_data.get('notes') else ''}
                    </div>
            """
        
        html_body += f"""
                    <div style="text-align: center; margin-top: 20px;">
                        <p style="color: #94a3b8; font-size: 13px;">
                            💡 Need to reschedule or cancel? Contact us at <strong style="color: #38bdf8;">(02) 8123 4567</strong>
                        </p>
                    </div>
                </div>
                <div class="footer">
                    <p>📍 <span class="address">48 B. Serrano St., Caloocan City</span></p>
                    <p>📞 (02) 8123 4567 | ✉️ petlink@clinic.com</p>
                    <p style="margin-top: 10px;">© 2026 PetLink Canine Distemper Center | All Rights Reserved</p>
                    <p style="font-size: 11px; margin-top: 5px;">This is an automated message. Please do not reply to this email.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        msg.html = html_body
        mail.send(msg)
        print(f"Email sent successfully to {recipient}")
        return True
    except Exception as e:
        print(f"Email error: {e}")
        return False

# ── Appointment Email Functions ──────────────────────────────────────
def send_booking_confirmation(email, appointment_data):
    subject = "✅ Appointment Booked Successfully!"
    body = """
    Thank you for booking an appointment with PetLink Canine Distemper Center!

    Your appointment has been received and is currently pending confirmation.
    You will receive another email once our staff confirms your appointment.

    📌 Please wait for our confirmation email.
    """
    return send_email_notification(email, subject, body, appointment_data)

def send_appointment_confirmation(email, appointment_data):
    subject = "✅ Appointment Confirmed!"
    body = """
    Great news! Your appointment has been confirmed by our staff.

    Please make sure to arrive on time for your scheduled appointment.
    If you need to reschedule or cancel, please contact us immediately.
    """
    return send_email_notification(email, subject, body, appointment_data)

def send_appointment_completion(email, appointment_data):
    subject = "✅ Appointment Completed!"
    body = """
    Your appointment has been successfully completed.

    Thank you for choosing PetLink Canine Distemper Center!
    We hope to see you and your pet again soon.

    Your pet's health and happiness are our top priority.
    """
    return send_email_notification(email, subject, body, appointment_data)

def send_appointment_cancellation(email, appointment_data):
    subject = "❌ Appointment Cancelled"
    body = """
    Your appointment has been cancelled.

    If you did not request this cancellation, please contact us immediately.
    We're here to help with any questions or concerns.

    We hope to serve you and your pet in the future.
    """
    return send_email_notification(email, subject, body, appointment_data)

# ── Routes ─────────────────────────────────────────────────────────────
@app.route('/')
def index():
    return render_template('index.html')

# ── REGISTER ROUTE ────────────────────────────────────────────────────
@app.route('/register', methods=["GET", "POST"])
@role_required("admin", "staff")
def register():
    if request.method == "POST":
        data = request.get_json()
        email = data.get("email", "").strip().lower()
        password = data.get("password", "")
        role = data.get("role", "user")
        phone = data.get("phone", "").strip()
        address = data.get("address", "").strip()
        
        current_user_role = request.current_user.get("role")
        
        if current_user_role == "staff" and role != "user":
            return jsonify({"success": False, "message": "Staff can only create customer accounts."})
        if role == "admin" and current_user_role != "admin":
            return jsonify({"success": False, "message": "Only admin can create admin accounts."})
        if current_user_role == "staff" and role in ["staff", "vet"]:
            return jsonify({"success": False, "message": "Staff cannot create staff or veterinarian accounts."})

        if not email or not password:
            return jsonify({"success": False, "message": "Email and password are required."})
        if not is_valid_email(email):
            return jsonify({"success": False, "message": "Please enter a valid email address."})
        if phone and not is_valid_phone(phone):
            return jsonify({"success": False, "message": "Please enter a valid Philippine phone number."})
        
        ok, err = is_strong_password(password)
        if not ok:
            return jsonify({"success": False, "message": err})

        conn = get_db()
        existing = conn.execute("SELECT id FROM users WHERE email=?", (email,)).fetchone()
        if existing:
            conn.close()
            return jsonify({"success": False, "message": "Email already registered!"})

        salt = generate_salt()
        hashed = hash_password(password, salt)
        
        if role not in ["user", "admin", "staff", "vet"]:
            role = "user"
            
        conn.execute(
            "INSERT INTO users (email, salt, hashed_password, role, phone, address, created_at) VALUES (?,?,?,?,?,?,?)",
            (email, salt, hashed, role, phone, address, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": "Registration successful!"})

    return render_template('register.html')

# ── LOGIN ROUTE ───────────────────────────────────────────────────────
@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        data = request.get_json()
        email = data.get("email", "").strip().lower()
        password = data.get("password", "")

        is_locked, remaining, failed_count = get_lockout_status(email)
        if is_locked:
            mins = remaining // 60
            secs = remaining % 60
            return jsonify({
                "success": False,
                "message": f"Account locked. Try again in {mins}m {secs}s.",
                "locked": True,
                "remaining": remaining
            })

        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
        conn.close()

        if not user:
            record_attempt(email, False)
            return jsonify({"success": False, "message": "Invalid email or password!"})

        input_hash = hash_password(password, user["salt"])
        if input_hash != user["hashed_password"]:
            record_attempt(email, False)
            attempts_left = MAX_ATTEMPTS - (failed_count + 1)
            msg = "Invalid email or password!"
            if attempts_left > 0:
                msg += f" {attempts_left} attempt(s) remaining."
            else:
                msg = f"Account locked for {LOCKOUT_MINUTES} minutes."
            return jsonify({"success": False, "message": msg})

        record_attempt(email, True)
        token = generate_jwt(email, user["role"])
        session["jwt_token"] = token
        session["username"] = user["email"]
        session["role"] = user["role"]
        
        # Determine redirect URL based on role
        if user["role"] == "admin":
            redirect_url = "/admin"
        elif user["role"] == "staff":
            redirect_url = "/staff"
        elif user["role"] == "vet":
            redirect_url = "/vet"
        else:
            redirect_url = "/dashboard"
        
        return jsonify({
            "success": True,
            "message": "Login successful!",
            "token": token,
            "role": user["role"],
            "redirect_url": redirect_url
        })

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/dashboard')
@jwt_required
def dashboard():
    user = request.current_user
    return render_template('dashboard.html', 
                         username=user["sub"], 
                         role=user["role"])

# ── ADMIN ROUTES ──────────────────────────────────────────────────────
@app.route('/admin')
@role_required("admin")
def admin_panel():
    conn = get_db()
    users = conn.execute("SELECT id, email, role, phone, address, created_at FROM users").fetchall()
    conn.close()
    return render_template('admin.html', users=[dict(u) for u in users])

@app.route('/api/users')
@role_required("admin")
def api_users():
    conn = get_db()
    users = conn.execute("SELECT id, email, role, phone, address, created_at FROM users").fetchall()
    conn.close()
    return jsonify({"success": True, "users": [dict(u) for u in users]})

@app.route('/api/promote', methods=["POST"])
@role_required("admin")
def promote_user():
    data = request.get_json()
    target = data.get("email")
    new_role = data.get("role", "user")
    if new_role not in ("user", "admin", "staff", "vet"):
        return jsonify({"success": False, "message": "Invalid role."})
    conn = get_db()
    conn.execute("UPDATE users SET role=? WHERE email=?", (new_role, target))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "message": f"{target} is now a {new_role}."})

# ── STAFF PANEL ROUTE ────────────────────────────────────────────────
@app.route('/staff')
@role_required("admin", "staff")
def staff_panel():
    conn = get_db()
    users = conn.execute("SELECT id, email, role, phone, address, created_at FROM users").fetchall()
    customers = [u for u in users if u["role"] == "user"]
    
    pets = conn.execute("SELECT COUNT(*) as count FROM pets").fetchone()
    total_pets = pets["count"] if pets else 0
    
    total_customers = len(customers)
    total_staff = len([u for u in users if u["role"] == "staff"])
    total_vets = len([u for u in users if u["role"] == "vet"])
    
    conn.close()
    current_role = session.get("role", "user")
    
    return render_template('staff.html', 
                         customers=customers,
                         total_customers=total_customers,
                         total_pets=total_pets,
                         total_staff=total_staff,
                         total_vets=total_vets,
                         role=current_role)

# ── VET PANEL ROUTE ──────────────────────────────────────────────────
@app.route('/vet')
@role_required("vet")
def vet_panel():
    return render_template('vet.html')

# ── PET MANAGEMENT ROUTES ─────────────────────────────────────────────
@app.route('/api/pets')
@role_required("admin", "staff", "vet")
def get_pets():
    conn = get_db()
    pets = conn.execute("""
        SELECT p.*, u.email as owner_email 
        FROM pets p
        JOIN users u ON p.customer_email = u.email
        ORDER BY p.created_at DESC
    """).fetchall()
    conn.close()
    return jsonify({"success": True, "pets": [dict(p) for p in pets]})

@app.route('/api/pets/<customer_email>')
@jwt_required
def get_pets_by_customer(customer_email):
    conn = get_db()
    pets = conn.execute(
        "SELECT * FROM pets WHERE customer_email = ? ORDER BY created_at DESC",
        (customer_email,)
    ).fetchall()
    conn.close()
    return jsonify({"success": True, "pets": [dict(p) for p in pets]})

@app.route('/api/pets', methods=["POST"])
@role_required("admin", "staff")
def create_pet():
    data = request.get_json()
    
    customer_email = data.get("customer_email", "").strip()
    pet_type = data.get("pet_type", "Dog").strip()
    name = data.get("name", "").strip()
    breed = data.get("breed", "").strip()
    age = data.get("age")
    gender = data.get("gender", "").strip()
    color = data.get("color", "").strip()
    weight = data.get("weight")
    medical_history = data.get("medical_history", "").strip()
    allergies = data.get("allergies", "").strip()
    pet_image = data.get("pet_image", "").strip()
    
    if not customer_email or not name:
        return jsonify({"success": False, "message": "Customer email and pet name are required."})
    
    conn = get_db()
    customer = conn.execute("SELECT id FROM users WHERE email = ?", (customer_email,)).fetchone()
    if not customer:
        conn.close()
        return jsonify({"success": False, "message": "Customer not found."})
    
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn.execute("""
        INSERT INTO pets (customer_email, pet_type, name, breed, age, gender, color, weight, medical_history, allergies, pet_image, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (customer_email, pet_type, name, breed, age, gender, color, weight, medical_history, allergies, pet_image, now, now))
    conn.commit()
    conn.close()
    
    return jsonify({"success": True, "message": "Pet created successfully!"})

@app.route('/api/pets/<int:pet_id>', methods=["PUT"])
@role_required("admin", "staff")
def update_pet(pet_id):
    data = request.get_json()
    
    pet_type = data.get("pet_type", "Dog").strip()
    name = data.get("name", "").strip()
    breed = data.get("breed", "").strip()
    age = data.get("age")
    gender = data.get("gender", "").strip()
    color = data.get("color", "").strip()
    weight = data.get("weight")
    medical_history = data.get("medical_history", "").strip()
    allergies = data.get("allergies", "").strip()
    pet_image = data.get("pet_image", "").strip()
    
    if not name:
        return jsonify({"success": False, "message": "Pet name is required."})
    
    conn = get_db()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    if pet_image:
        conn.execute("""
            UPDATE pets 
            SET pet_type = ?, name = ?, breed = ?, age = ?, gender = ?, color = ?, 
                weight = ?, medical_history = ?, allergies = ?, pet_image = ?, updated_at = ?
            WHERE id = ?
        """, (pet_type, name, breed, age, gender, color, weight, medical_history, allergies, pet_image, now, pet_id))
    else:
        conn.execute("""
            UPDATE pets 
            SET pet_type = ?, name = ?, breed = ?, age = ?, gender = ?, color = ?, 
                weight = ?, medical_history = ?, allergies = ?, updated_at = ?
            WHERE id = ?
        """, (pet_type, name, breed, age, gender, color, weight, medical_history, allergies, now, pet_id))
    
    conn.commit()
    conn.close()
    
    return jsonify({"success": True, "message": "Pet updated successfully!"})

@app.route('/api/pets/<int:pet_id>', methods=["DELETE"])
@role_required("admin", "staff")
def delete_pet(pet_id):
    conn = get_db()
    conn.execute("DELETE FROM pets WHERE id = ?", (pet_id,))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "message": "Pet deleted successfully!"})

# ── UPDATE PET IMAGE (Customer only) ──────────────────────────────────
@app.route('/api/pets/<int:pet_id>/image', methods=["PUT"])
@jwt_required
def update_pet_image(pet_id):
    """Allow customers to update only their pet's image."""
    data = request.get_json()
    email = request.current_user.get("sub")
    pet_image = data.get("pet_image", "").strip()
    
    # Check if pet belongs to customer
    conn = get_db()
    pet = conn.execute(
        "SELECT id, customer_email FROM pets WHERE id = ?",
        (pet_id,)
    ).fetchone()
    
    if not pet:
        conn.close()
        return jsonify({"success": False, "message": "Pet not found."})
    
    if pet["customer_email"] != email:
        # Check if user is admin or staff (they can edit any pet)
        role = request.current_user.get("role")
        if role not in ["admin", "staff"]:
            conn.close()
            return jsonify({"success": False, "message": "You are not authorized to edit this pet."})
    
    # Update only the image
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn.execute(
        "UPDATE pets SET pet_image = ?, updated_at = ? WHERE id = ?",
        (pet_image, now, pet_id)
    )
    conn.commit()
    conn.close()
    
    return jsonify({"success": True, "message": "Pet image updated successfully!"})

@app.route('/api/customers')
@role_required("admin", "staff")
def get_customers():
    conn = get_db()
    customers = conn.execute(
        "SELECT email, phone, address FROM users WHERE role = 'user' ORDER BY email"
    ).fetchall()
    conn.close()
    return jsonify({"success": True, "customers": [dict(c) for c in customers]})

# ── MEDICAL RECORDS ROUTES (Veterinarian) ─────────────────────────────

# Get all medical records
@app.route('/api/medical-records')
@role_required("vet", "admin")
def get_medical_records():
    conn = get_db()
    records = conn.execute("""
        SELECT mr.*, p.name as pet_name, p.pet_type, u.email as vet_email
        FROM medical_records mr
        JOIN pets p ON mr.pet_id = p.id
        JOIN users u ON mr.vet_email = u.email
        ORDER BY mr.visit_date DESC
    """).fetchall()
    conn.close()
    return jsonify({"success": True, "records": [dict(r) for r in records]})

# Get medical records for a specific pet
@app.route('/api/medical-records/pet/<int:pet_id>')
@role_required("vet", "admin")
def get_pet_medical_records(pet_id):
    conn = get_db()
    records = conn.execute("""
        SELECT mr.*, u.email as vet_email
        FROM medical_records mr
        JOIN users u ON mr.vet_email = u.email
        WHERE mr.pet_id = ?
        ORDER BY mr.visit_date DESC
    """, (pet_id,)).fetchall()
    conn.close()
    return jsonify({"success": True, "records": [dict(r) for r in records]})

# Create medical record
@app.route('/api/medical-records', methods=["POST"])
@role_required("vet")
def create_medical_record():
    data = request.get_json()
    vet_email = request.current_user.get("sub")
    
    pet_id = data.get("pet_id")
    visit_date = data.get("visit_date", "").strip()
    diagnosis = data.get("diagnosis", "").strip()
    treatment = data.get("treatment", "").strip()
    prescription = data.get("prescription", "").strip()
    notes = data.get("notes", "").strip()
    
    if not pet_id or not visit_date or not diagnosis:
        return jsonify({"success": False, "message": "Pet, visit date, and diagnosis are required."})
    
    # Check if pet exists
    conn = get_db()
    pet = conn.execute("SELECT id FROM pets WHERE id = ?", (pet_id,)).fetchone()
    if not pet:
        conn.close()
        return jsonify({"success": False, "message": "Pet not found."})
    
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn.execute("""
        INSERT INTO medical_records (pet_id, vet_email, visit_date, diagnosis, treatment, prescription, notes, status, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, 'active', ?, ?)
    """, (pet_id, vet_email, visit_date, diagnosis, treatment, prescription, notes, now, now))
    conn.commit()
    conn.close()
    
    return jsonify({"success": True, "message": "Medical record saved successfully!"})

# Update medical record
@app.route('/api/medical-records/<int:record_id>', methods=["PUT"])
@role_required("vet")
def update_medical_record(record_id):
    data = request.get_json()
    
    diagnosis = data.get("diagnosis", "").strip()
    treatment = data.get("treatment", "").strip()
    prescription = data.get("prescription", "").strip()
    notes = data.get("notes", "").strip()
    status = data.get("status", "active").strip()
    
    if not diagnosis:
        return jsonify({"success": False, "message": "Diagnosis is required."})
    
    conn = get_db()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn.execute("""
        UPDATE medical_records 
        SET diagnosis = ?, treatment = ?, prescription = ?, notes = ?, status = ?, updated_at = ?
        WHERE id = ?
    """, (diagnosis, treatment, prescription, notes, status, now, record_id))
    conn.commit()
    conn.close()
    
    return jsonify({"success": True, "message": "Medical record updated successfully!"})

# ── ML RECOMMENDATIONS ROUTES ──────────────────────────────────────────

# Get ML recommendations for validation
@app.route('/api/ml-recommendations')
@role_required("vet", "admin")
def get_ml_recommendations():
    conn = get_db()
    recommendations = conn.execute("""
        SELECT ml.*, p.name as pet_name, p.pet_type, p.breed, p.age
        FROM ml_recommendations ml
        JOIN pets p ON ml.pet_id = p.id
        WHERE ml.status = 'pending'
        ORDER BY ml.created_at DESC
    """).fetchall()
    conn.close()
    return jsonify({"success": True, "recommendations": [dict(r) for r in recommendations]})

# Create ML recommendation (for future AI integration)
@app.route('/api/ml-recommendations', methods=["POST"])
@role_required("vet", "admin")
def create_ml_recommendation():
    data = request.get_json()
    
    pet_id = data.get("pet_id")
    recommendation_type = data.get("recommendation_type", "").strip()
    recommendation_text = data.get("recommendation_text", "").strip()
    confidence_score = data.get("confidence_score", 0.0)
    
    if not pet_id or not recommendation_type or not recommendation_text:
        return jsonify({"success": False, "message": "All fields are required."})
    
    conn = get_db()
    pet = conn.execute("SELECT id FROM pets WHERE id = ?", (pet_id,)).fetchone()
    if not pet:
        conn.close()
        return jsonify({"success": False, "message": "Pet not found."})
    
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn.execute("""
        INSERT INTO ml_recommendations (pet_id, recommendation_type, recommendation_text, confidence_score, status, created_at)
        VALUES (?, ?, ?, ?, 'pending', ?)
    """, (pet_id, recommendation_type, recommendation_text, confidence_score, now))
    conn.commit()
    conn.close()
    
    return jsonify({"success": True, "message": "ML recommendation created!"})

# Validate ML recommendation (Vet approval)
@app.route('/api/ml-recommendations/<int:rec_id>/validate', methods=["PUT"])
@role_required("vet")
def validate_ml_recommendation(rec_id):
    data = request.get_json()
    status = data.get("status", "validated").strip()
    vet_notes = data.get("vet_notes", "").strip()
    
    if status not in ["validated", "rejected"]:
        return jsonify({"success": False, "message": "Invalid status."})
    
    conn = get_db()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn.execute("""
        UPDATE ml_recommendations 
        SET status = ?, vet_notes = ?, validated_at = ?
        WHERE id = ?
    """, (status, vet_notes, now, rec_id))
    conn.commit()
    conn.close()
    
    return jsonify({"success": True, "message": f"ML recommendation {status}!"})

# ── APPOINTMENT ROUTES ────────────────────────────────────────────────

# Get all services
@app.route('/api/services')
def get_services():
    conn = get_db()
    services = conn.execute(
        "SELECT * FROM services WHERE is_active = 1 ORDER BY name"
    ).fetchall()
    conn.close()
    return jsonify({"success": True, "services": [dict(s) for s in services]})

# Get appointments for a customer
@app.route('/api/appointments')
@jwt_required
def get_appointments():
    email = request.current_user.get("sub")
    conn = get_db()
    appointments = conn.execute("""
        SELECT a.*, p.name as pet_name, s.name as service_name, s.price, s.duration
        FROM appointments a
        JOIN pets p ON a.pet_id = p.id
        JOIN services s ON a.service_type = s.name
        WHERE a.customer_email = ?
        ORDER BY a.appointment_date DESC, a.appointment_time DESC
    """, (email,)).fetchall()
    conn.close()
    return jsonify({"success": True, "appointments": [dict(a) for a in appointments]})

# Get all appointments (for staff/admin)
@app.route('/api/appointments/all')
@role_required("admin", "staff")
def get_all_appointments():
    conn = get_db()
    appointments = conn.execute("""
        SELECT a.*, p.name as pet_name, u.email as customer_email, s.name as service_name
        FROM appointments a
        JOIN pets p ON a.pet_id = p.id
        JOIN users u ON a.customer_email = u.email
        JOIN services s ON a.service_type = s.name
        ORDER BY a.appointment_date DESC, a.appointment_time DESC
    """).fetchall()
    conn.close()
    return jsonify({"success": True, "appointments": [dict(a) for a in appointments]})

# Create appointment
@app.route('/api/appointments', methods=["POST"])
@jwt_required
def create_appointment():
    data = request.get_json()
    email = request.current_user.get("sub")
    
    pet_id = data.get("pet_id")
    service_type = data.get("service_type", "").strip()
    appointment_date = data.get("appointment_date", "").strip()
    appointment_time = data.get("appointment_time", "").strip()
    notes = data.get("notes", "").strip()
    
    if not pet_id or not service_type or not appointment_date or not appointment_time:
        return jsonify({"success": False, "message": "All fields are required."})
    
    # Check if pet belongs to customer
    conn = get_db()
    pet = conn.execute(
        "SELECT id FROM pets WHERE id = ? AND customer_email = ?",
        (pet_id, email)
    ).fetchone()
    if not pet:
        conn.close()
        return jsonify({"success": False, "message": "Pet not found or does not belong to you."})
    
    # Check if service exists
    service = conn.execute(
        "SELECT name FROM services WHERE name = ? AND is_active = 1",
        (service_type,)
    ).fetchone()
    if not service:
        conn.close()
        return jsonify({"success": False, "message": "Service not available."})
    
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn.execute("""
        INSERT INTO appointments (customer_email, pet_id, service_type, appointment_date, appointment_time, notes, status, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, 'pending', ?, ?)
    """, (email, pet_id, service_type, appointment_date, appointment_time, notes, now, now))
    conn.commit()
    conn.close()
    
    # Get appointment details for email
    appointment_data = {
        'pet_name': pet['name'] if pet else 'N/A',
        'service': service_type,
        'date': appointment_date,
        'time': appointment_time,
        'status': 'pending',
        'notes': notes
    }
    
    # Send confirmation email
    send_booking_confirmation(email, appointment_data)
    
    return jsonify({"success": True, "message": "Appointment booked successfully! Please wait for confirmation."})

# ── UPDATE APPOINTMENT STATUS (WITH EMAIL NOTIFICATIONS) ────────────
@app.route('/api/appointments/<int:appointment_id>/status', methods=["PUT"])
@role_required("admin", "staff")
def update_appointment_status(appointment_id):
    data = request.get_json()
    status = data.get("status", "").strip()
    
    if status not in ["pending", "confirmed", "completed", "cancelled"]:
        return jsonify({"success": False, "message": "Invalid status."})
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Get appointment details including customer email and pet info
        cursor.execute("""
            SELECT a.*, p.name as pet_name, u.email as customer_email
            FROM appointments a
            JOIN pets p ON a.pet_id = p.id
            JOIN users u ON a.customer_email = u.email
            WHERE a.id = ?
        """, (appointment_id,))
        appointment = cursor.fetchone()
        
        if not appointment:
            conn.close()
            return jsonify({"success": False, "message": "Appointment not found."})
        
        # Update status
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute(
            "UPDATE appointments SET status = ?, updated_at = ? WHERE id = ?",
            (status, now, appointment_id)
        )
        conn.commit()
        
        # ── Send email notification to customer ────────────────────────
        appointment_data = {
            'pet_name': appointment["pet_name"],
            'service': appointment["service_type"],
            'date': appointment["appointment_date"],
            'time': appointment["appointment_time"],
            'status': status,
            'notes': appointment["notes"]
        }
        
        email_sent = False
        
        if status == "confirmed":
            email_sent = send_appointment_confirmation(appointment["customer_email"], appointment_data)
        elif status == "completed":
            email_sent = send_appointment_completion(appointment["customer_email"], appointment_data)
        elif status == "cancelled":
            email_sent = send_appointment_cancellation(appointment["customer_email"], appointment_data)
        
        if email_sent:
            message = f"Appointment {status}! Email notification sent to customer."
        else:
            message = f"Appointment {status}! (Note: Email could not be sent. Please verify email configuration.)"
        
    except Exception as e:
        conn.rollback()
        print(f"Error updating appointment: {e}")
        conn.close()
        return jsonify({"success": False, "message": "An error occurred."})
    
    conn.close()
    return jsonify({"success": True, "message": message})

# Cancel appointment (customer can cancel pending appointments)
@app.route('/api/appointments/<int:appointment_id>/cancel', methods=["PUT"])
@jwt_required
def cancel_appointment(appointment_id):
    email = request.current_user.get("sub")
    
    conn = get_db()
    appointment = conn.execute(
        "SELECT status FROM appointments WHERE id = ? AND customer_email = ?",
        (appointment_id, email)
    ).fetchone()
    
    if not appointment:
        conn.close()
        return jsonify({"success": False, "message": "Appointment not found."})
    
    if appointment["status"] == "completed":
        conn.close()
        return jsonify({"success": False, "message": "Cannot cancel a completed appointment."})
    
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn.execute(
        "UPDATE appointments SET status = 'cancelled', updated_at = ? WHERE id = ?",
        (now, appointment_id)
    )
    conn.commit()
    conn.close()
    
    return jsonify({"success": True, "message": "Appointment cancelled successfully."})

# Delete appointment (admin only)
@app.route('/api/appointments/<int:appointment_id>', methods=["DELETE"])
@role_required("admin")
def delete_appointment(appointment_id):
    conn = get_db()
    conn.execute("DELETE FROM appointments WHERE id = ?", (appointment_id,))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "message": "Appointment deleted successfully."})

# ── GUEST BOOKING ROUTE ────────────────────────────────────────────────

@app.route('/booking')
def booking():
    return render_template('booking.html')

@app.route('/api/guest-booking', methods=["POST"])
def guest_booking():
    data = request.get_json()
    
    name = data.get("name", "").strip()
    email = data.get("email", "").strip().lower()
    phone = data.get("phone", "").strip()
    pet_name = data.get("pet_name", "").strip()
    pet_type = data.get("pet_type", "Dog").strip()
    breed = data.get("breed", "").strip()
    age = data.get("age")
    gender = data.get("gender", "").strip()
    service_type = data.get("service_type", "").strip()
    appointment_date = data.get("appointment_date", "").strip()
    appointment_time = data.get("appointment_time", "").strip()
    notes = data.get("notes", "").strip()
    
    # Validate required fields
    if not name or not email or not phone or not pet_name or not service_type or not appointment_date or not appointment_time:
        return jsonify({"success": False, "message": "All required fields must be filled."})
    
    conn = get_db()
    cursor = conn.cursor()
    pet_id = None
    customer_email = email
    
    try:
        # Check if customer already exists (by email)
        cursor.execute("SELECT id, email FROM users WHERE email = ?", (email,))
        customer = cursor.fetchone()
        
        if not customer:
            # Create a guest customer account
            salt = generate_salt()
            temp_password = secrets.token_urlsafe(8)
            hashed = hash_password(temp_password, salt)
            
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("""
                INSERT INTO users (email, salt, hashed_password, role, phone, address, created_at)
                VALUES (?, ?, ?, 'user', ?, '', ?)
            """, (email, salt, hashed, phone, now))
            customer_email = email
        
        # Check if pet already exists (by name and owner)
        cursor.execute(
            "SELECT id, name FROM pets WHERE name = ? AND customer_email = ?",
            (pet_name, customer_email)
        )
        pet = cursor.fetchone()
        
        if pet:
            pet_id = pet["id"]
        else:
            # Create new pet
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("""
                INSERT INTO pets (customer_email, pet_type, name, breed, age, gender, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (customer_email, pet_type, pet_name, breed, age, gender, now, now))
            pet_id = cursor.lastrowid
        
        # Create appointment
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
            INSERT INTO appointments (customer_email, pet_id, service_type, appointment_date, appointment_time, notes, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, 'pending', ?, ?)
        """, (customer_email, pet_id, service_type, appointment_date, appointment_time, notes, now, now))
        
        conn.commit()
        
        # ── Send confirmation email ────────────────────────────────────
        appointment_data = {
            'pet_name': pet_name,
            'service': service_type,
            'date': appointment_date,
            'time': appointment_time,
            'status': 'pending',
            'notes': notes
        }
        send_booking_confirmation(email, appointment_data)
        
    except Exception as e:
        conn.rollback()
        print(f"Error in guest booking: {e}")
        return jsonify({"success": False, "message": "An error occurred while booking. Please try again."})
    finally:
        conn.close()
    
    return jsonify({
        "success": True,
        "message": "Appointment booked successfully! A confirmation email has been sent to your email address."
    })

# ── FORGOT PASSWORD ROUTES ────────────────────────────────────────────
@app.route('/forgot-password', methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        data = request.get_json()
        email = data.get("email", "").strip().lower()

        conn = get_db()
        user = conn.execute("SELECT id FROM users WHERE email=?", (email,)).fetchone()

        if user:
            token = secrets.token_urlsafe(32)
            expires_at = (datetime.now(timezone.utc) + timedelta(minutes=15)).isoformat()
            conn.execute(
                "INSERT INTO reset_tokens (email, token, expires_at, used) VALUES (?,?,?,0)",
                (email, token, expires_at)
            )
            conn.commit()
            reset_link = f"http://localhost:5000/reset-password?token={token}"
            conn.close()
            return jsonify({
                "success": True,
                "message": "If that email exists, a reset link has been generated.",
                "reset_link": reset_link
            })
        conn.close()
        return jsonify({"success": True, "message": "If that email exists, a reset link has been generated."})

    return render_template('forgot_password.html')

@app.route('/reset-password', methods=["GET", "POST"])
def reset_password():
    if request.method == "GET":
        token = request.args.get("token", "")
        return render_template('reset_password.html', token=token)

    data = request.get_json()
    token = data.get("token", "")
    new_password = data.get("password", "")

    ok, err = is_strong_password(new_password)
    if not ok:
        return jsonify({"success": False, "message": err})

    conn = get_db()
    record = conn.execute(
        "SELECT * FROM reset_tokens WHERE token=? AND used=0", (token,)
    ).fetchone()

    if not record:
        conn.close()
        return jsonify({"success": False, "message": "Invalid or already-used reset token."})

    expires_at = datetime.fromisoformat(record["expires_at"])
    if datetime.now(timezone.utc) > expires_at:
        conn.close()
        return jsonify({"success": False, "message": "Reset token has expired. Please request a new one."})

    salt = generate_salt()
    hashed = hash_password(new_password, salt)
    conn.execute("UPDATE users SET salt=?, hashed_password=? WHERE email=?",
                 (salt, hashed, record["email"]))
    conn.execute("UPDATE reset_tokens SET used=1 WHERE token=?", (token,))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "message": "Password reset successful! You can now sign in."})

@app.route('/api/verify-token', methods=["POST"])
def verify_token():
    data = request.get_json()
    token = data.get("token", "")
    payload = verify_jwt(token)
    if payload:
        return jsonify({"success": True, "payload": payload})
    return jsonify({"success": False, "message": "Invalid or expired token."})

if __name__ == "__main__":
    init_db()
    app.run(debug=True)