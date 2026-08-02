// Create floating particles
function createParticles() {
  const particlesContainer = document.getElementById('particles');
  for (let i = 0; i < 50; i++) {
    const particle = document.createElement('div');
    particle.classList.add('particle');
    const size = Math.random() * 5 + 2;
    particle.style.width = `${size}px`;
    particle.style.height = `${size}px`;
    particle.style.left = `${Math.random() * 100}%`;
    particle.style.top = `${Math.random() * 100}%`;
    particle.style.animationDelay = `${Math.random() * 15}s`;
    particle.style.animationDuration = `${Math.random() * 10 + 10}s`;
    particlesContainer.appendChild(particle);
  }
}
createParticles();

// Load saved email if remembered
const saved = localStorage.getItem('rememberedEmail');
if (saved) {
  const emailInput = document.getElementById('email');
  if (emailInput) {
    emailInput.value = saved;
  }
  const rememberCheck = document.getElementById('rememberMe');
  if (rememberCheck) {
    rememberCheck.checked = true;
  }
}

let countdownInterval = null;

function toggleEye(inputId, btn) {
  const input = document.getElementById(inputId);
  if (!input) return;
  
  const isHidden = input.type === 'password';
  input.type = isHidden ? 'text' : 'password';
  btn.innerHTML = isHidden
    ? `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94"/><path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19"/><line x1="1" y1="1" x2="23" y2="23"/></svg>`
    : `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>`;
}

function startCountdown(seconds) {
  const cd = document.getElementById('countdown');
  const btn = document.getElementById('loginBtn');
  if (!cd || !btn) return;
  
  cd.style.display = 'block';
  btn.disabled = true;
  btn.style.opacity = '0.5';

  clearInterval(countdownInterval);
  let rem = seconds;
  const tick = () => {
    const m = Math.floor(rem / 60), s = rem % 60;
    cd.textContent = `🔒 Account locked — ${m}m ${String(s).padStart(2,'0')}s remaining`;
    if (rem <= 0) {
      clearInterval(countdownInterval);
      cd.style.display = 'none';
      btn.disabled = false;
      btn.style.opacity = '';
    }
    rem--;
  };
  tick();
  countdownInterval = setInterval(tick, 1000);
}

function showRedirectOverlay() {
  const role = localStorage.getItem('role') || sessionStorage.getItem('role') || 'user';
  let message = 'Welcome back! Redirecting to home...';
  let icon = '✓';
  
  if (role === 'admin') {
    message = 'Welcome Admin! Redirecting to Admin Panel...';
    icon = '⚙️';
  } else if (role === 'staff') {
    message = 'Welcome Staff! Redirecting to Staff Panel...';
    icon = '👨‍💼';
  } else if (role === 'vet') {
    message = 'Welcome Doctor! Redirecting to Dashboard...';
    icon = '🏥';
  } else {
    message = 'Welcome back! Redirecting to Dashboard...';
    icon = '🐾';
  }
  
  const overlay = document.createElement('div');
  overlay.className = 'redirect-overlay';
  overlay.innerHTML = `
    <div class="redirect-content">
      <h3 style="color: #38bdf8; margin-bottom: 15px; font-size: 40px;">${icon}</h3>
      <h3 style="color: #38bdf8; margin-bottom: 15px;">Login Successful!</h3>
      <p style="color: #94a3b8; margin-bottom: 20px;">${message}</p>
      <div class="redirect-spinner"></div>
    </div>
  `;
  document.body.appendChild(overlay);
  
  setTimeout(() => {
    if (overlay && overlay.parentNode) {
      overlay.remove();
    }
  }, 1500);
}

async function handleLogin() {
  const emailInput = document.getElementById('email');
  const passwordInput = document.getElementById('password');
  const rememberCheck = document.getElementById('rememberMe');
  const msg = document.getElementById('message');
  const btn = document.getElementById('loginBtn');
  const btnText = document.getElementById('btnText');
  
  // Check if elements exist
  if (!emailInput || !passwordInput) {
    console.error('Email or password input not found');
    return;
  }
  
  const email = emailInput.value.trim().toLowerCase();
  const password = passwordInput.value;
  const remember = rememberCheck ? rememberCheck.checked : false;
  
  const show = (text, type) => { 
    if (!msg) return;
    msg.textContent = text; 
    msg.className = 'message show ' + type; 
    setTimeout(() => {
      msg.classList.remove('show');
    }, 5000);
  };

  // Validate email format
  const emailPattern = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
  if (!email) {
    show('Please enter your email address.', 'error');
    return;
  }
  if (!emailPattern.test(email)) {
    show('Please enter a valid email address.', 'error');
    return;
  }
  if (!password) {
    show('Please enter your password.', 'error');
    return;
  }

  if (btn) {
    btnText.innerHTML = 'Signing in... <span class="loading"></span>';
    btn.disabled = true;
  }

  try {
    const res = await fetch('/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });
    const data = await res.json();
    
    if (btn) {
      btnText.innerHTML = 'Sign in';
      btn.disabled = false;
    }
    
    show(data.message, data.success ? 'success' : 'error');

    if (data.locked && data.remaining) {
      startCountdown(data.remaining);
    }

    if (data.success) {
      if (remember) {
        localStorage.setItem('rememberedEmail', email);
      } else {
        localStorage.removeItem('rememberedEmail');
      }
      
      localStorage.setItem('email', email);
      sessionStorage.setItem('email', email);
      
      if (data.token) {
        sessionStorage.setItem('jwt_token', data.token);
        localStorage.setItem('jwt_token', data.token);
      }
      
      sessionStorage.setItem('role', data.role);
      localStorage.setItem('role', data.role);
      
      showRedirectOverlay();
      
      const card = document.querySelector('.card');
      if (card) {
        card.style.animation = 'none';
        card.offsetHeight;
        card.style.animation = 'slideUpFade 0.6s cubic-bezier(0.34, 1.2, 0.64, 1)';
      }
      
      const redirectUrl = data.redirect_url || '/dashboard';
      setTimeout(() => {
        window.location.href = redirectUrl;
      }, 1500);
    }
  } catch (error) {
    console.error('Login error:', error);
    if (btn) {
      btnText.innerHTML = 'Sign in';
      btn.disabled = false;
    }
    show('Something went wrong. Please try again.', 'error');
  }
}

// Make handleLogin available globally
window.handleLogin = handleLogin;

// Add enter key support
document.addEventListener('keydown', function(e) {
  if (e.key === 'Enter') {
    const activeElement = document.activeElement;
    if (activeElement && (activeElement.id === 'email' || activeElement.id === 'password')) {
      handleLogin();
    }
  }
});

// Add input animation effects
const inputs = document.querySelectorAll('input');
inputs.forEach(input => {
  input.addEventListener('focus', () => {
    const wrap = input.parentElement;
    if (wrap) {
      wrap.style.transform = 'scale(1.02)';
    }
  });
  input.addEventListener('blur', () => {
    const wrap = input.parentElement;
    if (wrap) {
      wrap.style.transform = 'scale(1)';
    }
  });
});

// Verify that elements exist on page load
document.addEventListener('DOMContentLoaded', function() {
  const emailInput = document.getElementById('email');
  const passwordInput = document.getElementById('password');
  const loginBtn = document.getElementById('loginBtn');
  
  if (!emailInput) console.warn('Email input not found!');
  if (!passwordInput) console.warn('Password input not found!');
  if (!loginBtn) console.warn('Login button not found!');
  
  console.log('Login page loaded successfully');
});