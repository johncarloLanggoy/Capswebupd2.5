// Toggle sidebar collapse
function toggleSidebar() {
  const sidebar = document.getElementById('sidebar');
  const main = document.getElementById('mainContent');
  const toggleBtn = document.querySelector('.toggle-sidebar');
  
  sidebar.classList.toggle('collapsed');
  main.classList.toggle('expanded');
  
  if (sidebar.classList.contains('collapsed')) {
    toggleBtn.innerHTML = '▶';
  } else {
    toggleBtn.innerHTML = '◀';
  }
}

// Mobile sidebar toggle
function toggleMobileSidebar() {
  const sidebar = document.getElementById('sidebar');
  sidebar.classList.toggle('mobile-open');
}

// Close mobile sidebar when clicking outside
document.addEventListener('click', function(event) {
  const sidebar = document.getElementById('sidebar');
  const mobileBtn = document.querySelector('.mobile-menu-btn');
  if (window.innerWidth <= 768) {
    if (sidebar && mobileBtn && !sidebar.contains(event.target) && !mobileBtn.contains(event.target)) {
      sidebar.classList.remove('mobile-open');
    }
  }
});

// Show logout confirmation modal
function showLogoutModal() {
  const overlay = document.createElement('div');
  overlay.className = 'modal-overlay';
  
  overlay.innerHTML = `
    <div class="modal-popup">
      <div class="modal-icon">🚪</div>
      <h3>Logout Confirmation</h3>
      <p>Are you sure you want to logout? You'll need to sign in again to access your dashboard.</p>
      <div class="modal-buttons">
        <button class="modal-btn modal-btn-cancel" onclick="closeModal()">Cancel</button>
        <button class="modal-btn modal-btn-logout" onclick="confirmLogout()">Yes, Logout</button>
      </div>
    </div>
  `;
  
  document.body.appendChild(overlay);
  
  overlay.addEventListener('click', (e) => {
    if (e.target === overlay) {
      closeModal();
    }
  });
  
  const escHandler = (e) => {
    if (e.key === 'Escape') {
      closeModal();
      document.removeEventListener('keydown', escHandler);
    }
  };
  document.addEventListener('keydown', escHandler);
}

function closeModal() {
  const overlay = document.querySelector('.modal-overlay');
  if (overlay) {
    overlay.remove();
  }
}

async function confirmLogout() {
  closeModal();
  
  try {
    await fetch('/logout');
    sessionStorage.clear();
    localStorage.removeItem('rememberedUser');
    localStorage.removeItem('username');
    localStorage.removeItem('jwt_token');
    localStorage.removeItem('role');
    sessionStorage.removeItem('role');
    window.location.href = '/';
  } catch (error) {
    console.error('Logout error:', error);
    sessionStorage.clear();
    localStorage.removeItem('rememberedUser');
    localStorage.removeItem('username');
    localStorage.removeItem('jwt_token');
    localStorage.removeItem('role');
    sessionStorage.removeItem('role');
    window.location.href = '/';
  }
}

// Toggle Dashboard Dropdown
function toggleDashboardDropdown(event) {
  if (event) event.stopPropagation();
  const dropdownContent = document.getElementById('dropdownContent');
  const dropdownArrow = document.getElementById('dropdownArrow');
  
  if (dropdownContent && dropdownArrow) {
    dropdownContent.classList.toggle('show');
    dropdownArrow.classList.toggle('rotated');
  }
}

// Scroll to section function
function scrollToSection(sectionId) {
  const element = document.getElementById(sectionId);
  if (element) {
    const offset = 80;
    const elementPosition = element.getBoundingClientRect().top;
    const offsetPosition = elementPosition + window.pageYOffset - offset;
    
    window.scrollTo({
      top: offsetPosition,
      behavior: 'smooth'
    });
  }
  
  if (window.innerWidth <= 768) {
    const sidebar = document.getElementById('sidebar');
    if (sidebar) {
      sidebar.classList.remove('mobile-open');
    }
  }
}

// Initialize dropdown to be open by default on desktop
document.addEventListener('DOMContentLoaded', function() {
  const dropdownContent = document.getElementById('dropdownContent');
  const dropdownArrow = document.getElementById('dropdownArrow');
  if (dropdownContent && dropdownArrow && window.innerWidth > 768) {
    dropdownContent.classList.add('show');
    dropdownArrow.classList.add('rotated');
  }
});

// Close dropdown when clicking outside on mobile
document.addEventListener('click', function(event) {
  const dropdownContainer = document.querySelector('.dropdown-container');
  const dropdownContent = document.getElementById('dropdownContent');
  const dropdownArrow = document.getElementById('dropdownArrow');
  
  if (dropdownContainer && !dropdownContainer.contains(event.target) && window.innerWidth <= 768) {
    if (dropdownContent && dropdownContent.classList.contains('show')) {
      dropdownContent.classList.remove('show');
      if (dropdownArrow) dropdownArrow.classList.remove('rotated');
    }
  }
});

async function loadServices() {
  try {
    const res = await fetch('/api/services');
    const data = await res.json();
    if (data.success) {
      const select = document.getElementById('bookingService');
      select.innerHTML = '<option value="">Choose a service...</option>';
      data.services.forEach(service => {
        const option = document.createElement('option');
        option.value = service.name;
        option.textContent = `${service.name} (₱${service.price} - ${service.duration} min)`;
        select.appendChild(option);
      });
    }
  } catch (error) {
    console.error('Error loading services:', error);
  }
}

// ── Load Customer's Pets for Booking ────────────────────────────────
async function loadPetsForBooking() {
  const email = localStorage.getItem('email') || sessionStorage.getItem('email');
  if (!email) return;
  
  try {
    const res = await fetch(`/api/pets/${email}`);
    const data = await res.json();
    if (data.success) {
      const select = document.getElementById('bookingPet');
      select.innerHTML = '<option value="">Choose your pet...</option>';
      data.pets.forEach(pet => {
        const option = document.createElement('option');
        option.value = pet.id;
        const petType = pet.pet_type || 'Dog';
        const petIcon = petType === 'Cat' ? '🐈' : '🐕';
        option.textContent = `${petIcon} ${pet.name} (${pet.breed || 'Mixed Breed'})`;
        select.appendChild(option);
      });
    }
  } catch (error) {
    console.error('Error loading pets:', error);
  }
}

// ── Load Appointments ─────────────────────────────────────────────────
async function loadAppointments() {
  const container = document.getElementById('myAppointmentsContainer');
  
  try {
    const res = await fetch('/api/appointments');
    const data = await res.json();
    
    let total = 0, upcoming = 0, completed = 0;
    
    if (data.success && data.appointments && data.appointments.length > 0) {
      total = data.appointments.length;
      data.appointments.forEach(app => {
        if (app.status === 'pending' || app.status === 'confirmed') upcoming++;
        if (app.status === 'completed') completed++;
      });
      
      document.getElementById('appointmentCount').textContent = total;
      document.getElementById('upcomingCount').textContent = upcoming;
      document.getElementById('completedCount').textContent = completed;
      
      let html = '';
      data.appointments.forEach(app => {
        const statusClass = `status-${app.status}`;
        const statusLabel = app.status.charAt(0).toUpperCase() + app.status.slice(1);
        const canCancel = app.status === 'pending' || app.status === 'confirmed';
        
        html += `
          <div class="appointment-card">
            <div class="appointment-header">
              <div>
                <div class="appointment-pet">🐕 ${app.pet_name}</div>
                <div class="appointment-service">${app.service_name}</div>
              </div>
              <span class="appointment-status ${statusClass}">${statusLabel}</span>
            </div>
            <div class="appointment-details">
              <div>📅 ${app.appointment_date} at ${app.appointment_time}</div>
              <div>💰 ₱${app.price || '—'} • ⏱️ ${app.duration || '—'} min</div>
              ${app.notes ? `<div>📝 ${app.notes}</div>` : ''}
            </div>
            <div class="appointment-actions">
              ${canCancel ? `<button class="btn-cancel-appointment" onclick="cancelAppointment(${app.id})">Cancel</button>` : ''}
              <button class="btn-view-details" onclick="alert('Appointment details:\\nPet: ${app.pet_name}\\nService: ${app.service_name}\\nDate: ${app.appointment_date}\\nTime: ${app.appointment_time}\\nStatus: ${statusLabel}')">View Details</button>
            </div>
          </div>
        `;
      });
      container.innerHTML = html;
    } else {
      document.getElementById('appointmentCount').textContent = '0';
      document.getElementById('upcomingCount').textContent = '0';
      document.getElementById('completedCount').textContent = '0';
      container.innerHTML = `
        <div class="no-appointments">
          <div class="icon">📅</div>
          <h3>No Appointments</h3>
          <p>You haven't booked any appointments yet. Click "Book New Appointment" to get started!</p>
        </div>
      `;
    }
  } catch (error) {
    console.error('Error loading appointments:', error);
    container.innerHTML = `
      <div class="no-appointments" style="border-color: #ef4444;">
        <div class="icon">⚠️</div>
        <h3>Error Loading Appointments</h3>
        <p style="color: #ef4444;">There was a problem loading your appointments. Please refresh the page.</p>
      </div>
    `;
  }
}

// ── Book Appointment Modal ──────────────────────────────────────────
function showBookAppointmentModal() {
  document.getElementById('bookAppointmentModal').style.display = 'flex';
  loadServices();
  loadPetsForBooking();
  document.getElementById('bookingForm').reset();
  const today = new Date().toISOString().split('T')[0];
  document.getElementById('bookingDate').min = today;
}

function closeBookAppointmentModal() {
  document.getElementById('bookAppointmentModal').style.display = 'none';
}

async function submitAppointment(e) {
  e.preventDefault();
  
  const pet_id = document.getElementById('bookingPet').value;
  const service_type = document.getElementById('bookingService').value;
  const appointment_date = document.getElementById('bookingDate').value;
  const appointment_time = document.getElementById('bookingTime').value;
  const notes = document.getElementById('bookingNotes').value.trim();
  
  if (!pet_id || !service_type || !appointment_date || !appointment_time) {
    alert('Please fill in all required fields.');
    return;
  }
  
  try {
    const res = await fetch('/api/appointments', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ pet_id, service_type, appointment_date, appointment_time, notes })
    });
    const data = await res.json();
    
    if (data.success) {
      alert('✅ Appointment booked successfully! Please wait for confirmation.');
      closeBookAppointmentModal();
      loadAppointments();
    } else {
      alert('❌ ' + (data.message || 'Error booking appointment.'));
    }
  } catch (error) {
    console.error('Error:', error);
    alert('Something went wrong. Please try again.');
  }
}

// ── Cancel Appointment ──────────────────────────────────────────────
async function cancelAppointment(appointmentId) {
  if (!confirm('Are you sure you want to cancel this appointment?')) return;
  
  try {
    const res = await fetch(`/api/appointments/${appointmentId}/cancel`, {
      method: 'PUT'
    });
    const data = await res.json();
    
    if (data.success) {
      alert('✅ Appointment cancelled successfully.');
      loadAppointments();
    } else {
      alert('❌ ' + (data.message || 'Error cancelling appointment.'));
    }
  } catch (error) {
    console.error('Error:', error);
    alert('Something went wrong. Please try again.');
  }
}

// ── Load Customer's Pets ─────────────────────────────────────────────
async function loadMyPets() {
  const email = localStorage.getItem('email') || sessionStorage.getItem('email');
  if (!email) return;
  
  const container = document.getElementById('myPetsContainer');
  
  try {
    const res = await fetch(`/api/pets/${email}`);
    const data = await res.json();
    
    if (data.success && data.pets && data.pets.length > 0) {
      document.getElementById('petCount').textContent = data.pets.length;
      
      let petsHTML = '<div class="pets-grid">';
      data.pets.forEach(pet => {
        let statusClass = 'healthy';
        let statusText = '✅ Healthy';
        if (pet.medical_history) {
          statusClass = 'warning';
          statusText = '⚠️ Needs Attention';
        }
        if (pet.allergies) {
          statusClass = 'critical';
          statusText = '⚠️ Has Allergies';
        }
        
        // Determine pet type and icon
        const petType = pet.pet_type || 'Dog';
        const petIcon = petType === 'Cat' ? '🐈' : '🐕';
        const petTypeLabel = petType === 'Cat' ? 'Cat' : 'Dog';
        
        petsHTML += `
          <div class="pet-card">
            <div class="pet-avatar">
              ${pet.pet_image ? 
                `<img src="${pet.pet_image}" alt="${pet.name}" id="petImg-${pet.id}">` : 
                `<span style="font-size: 60px;">${petIcon}</span>`
              }
              <button class="edit-image-btn" onclick="showEditPetImageModal(${pet.id}, '${pet.name}')" title="Change pet photo">
                📷
              </button>
            </div>
            <div class="pet-name">${pet.name} ${petIcon}</div>
            <div class="pet-breed">${petTypeLabel} • ${pet.breed || 'Mixed Breed'} • ${pet.age || 'Unknown'} years</div>
            <div class="pet-info">
              <div><span class="label">🐾 Type:</span> ${petTypeLabel}</div>
              <div><span class="label">⚥ Gender:</span> ${pet.gender || '—'}</div>
              <div><span class="label">🎨 Color:</span> ${pet.color || '—'}</div>
              <div><span class="label">⚖️ Weight:</span> ${pet.weight || '—'} kg</div>
              ${pet.allergies ? `<div style="color: #ef4444;"><span class="label">⚠️ Allergies:</span> ${pet.allergies}</div>` : ''}
              ${pet.medical_history ? `<div style="color: #f59e0b;"><span class="label">📋 Medical History:</span> ${pet.medical_history}</div>` : ''}
              <div style="text-align: center; margin-top: 10px;">
                <span class="pet-status ${statusClass}">${statusText}</span>
              </div>
            </div>
          </div>
        `;
      });
      petsHTML += '</div>';
      container.innerHTML = petsHTML;
    } else {
      document.getElementById('petCount').textContent = '0';
      container.innerHTML = `
        <div class="no-pets-message">
          <div class="icon">🐕</div>
          <h3>No Pets Registered</h3>
          <p>You don't have any pets registered yet. Please visit our clinic to register your furry friend!</p>
          <div class="info-box">
            <p>📌 To register your pet:</p>
            <p>1. Visit our clinic at <span class="highlight">48 B. Serrano St., Caloocan City</span></p>
            <p>2. Our friendly staff will assist you with the registration</p>
          </div>
          <button class="visit-clinic-btn" onclick="alert('📍 PetLink Canine Distemper Center\\n48 B. Serrano St., Caloocan City')">
            📍 Visit Our Clinic
          </button>
        </div>
      `;
    }
  } catch (error) {
    console.error('Error loading pets:', error);
  }
}

// ── Edit Pet Image Modal ─────────────────────────────────────────────
let currentEditPetId = null;
let currentEditPetName = '';

function showEditPetImageModal(petId, petName) {
  currentEditPetId = petId;
  currentEditPetName = petName;
  document.getElementById('editPetImageId').value = petId;
  document.getElementById('editPetNameDisplay').textContent = petName;
  document.getElementById('editPetImageModal').style.display = 'flex';
  
  // Reset preview
  document.getElementById('editPetImagePreview2').innerHTML = '<span style="color: #64748b; font-size: 14px; text-align: center;">No<br>Image</span>';
  document.getElementById('editPetImageInput').value = '';
  
  // Load existing image if any - find the pet card's image
  const petCards = document.querySelectorAll('.pet-card');
  for (let card of petCards) {
    const nameEl = card.querySelector('.pet-name');
    if (nameEl && nameEl.textContent.trim().startsWith(petName)) {
      const img = card.querySelector('.pet-avatar img');
      if (img) {
        document.getElementById('editPetImagePreview2').innerHTML = `<img src="${img.src}" style="width: 100%; height: 100%; object-fit: cover;">`;
      }
      break;
    }
  }
  
  // Reset button
  document.getElementById('updatePhotoBtn').innerHTML = '💾 Update Photo';
  document.getElementById('updatePhotoBtn').disabled = false;
}

function closeEditPetImageModal() {
  document.getElementById('editPetImageModal').style.display = 'none';
}

function previewEditPetImage2(event) {
  const file = event.target.files[0];
  if (!file) return;
  
  // Check file size (max 5MB)
  if (file.size > 5 * 1024 * 1024) {
    alert('File is too large. Please upload an image under 5MB.');
    event.target.value = '';
    return;
  }
  
  const reader = new FileReader();
  reader.onload = function(e) {
    const preview = document.getElementById('editPetImagePreview2');
    preview.innerHTML = `<img src="${e.target.result}" style="width: 100%; height: 100%; object-fit: cover;">`;
  };
  reader.readAsDataURL(file);
}

async function submitPetImageUpdate(e) {
  e.preventDefault();
  
  const petId = document.getElementById('editPetImageId').value;
  const imageInput = document.getElementById('editPetImageInput');
  const btn = document.getElementById('updatePhotoBtn');
  
  if (!imageInput.files || !imageInput.files[0]) {
    alert('Please select a photo to upload.');
    return;
  }
  
  // Check file size (max 5MB)
  if (imageInput.files[0].size > 5 * 1024 * 1024) {
    alert('File is too large. Please upload an image under 5MB.');
    return;
  }
  
  // Show loading state
  btn.innerHTML = '⏳ Uploading...';
  btn.disabled = true;
  
  // Get base64 image
  const reader = new FileReader();
  reader.onload = async function(event) {
    const pet_image = event.target.result;
    
    try {
      const res = await fetch(`/api/pets/${petId}/image`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ pet_image })
      });
      const data = await res.json();
      
      if (data.success) {
        alert('✅ Pet photo updated successfully!');
        closeEditPetImageModal();
        loadMyPets(); // Reload pets to show new image
      } else {
        alert('❌ ' + (data.message || 'Error updating photo.'));
        btn.innerHTML = '💾 Update Photo';
        btn.disabled = false;
      }
    } catch (error) {
      console.error('Error:', error);
      alert('Something went wrong. Please try again.');
      btn.innerHTML = '💾 Update Photo';
      btn.disabled = false;
    }
  };
  reader.readAsDataURL(imageInput.files[0]);
}

// ── Logout ──────────────────────────────────────────────────────────
function showLogoutModal() {
  const overlay = document.createElement('div');
  overlay.className = 'modal-overlay';
  overlay.id = 'logoutModal';
  overlay.innerHTML = `
    <div class="modal-popup" style="max-width: 400px; text-align: center;">
      <div style="font-size: 48px; margin-bottom: 20px;">🚪</div>
      <h3 style="color: #38bdf8; font-size: 24px; margin-bottom: 10px;">Logout Confirmation</h3>
      <p style="color: #94a3b8; margin-bottom: 25px; line-height: 1.6;">Are you sure you want to logout? You'll need to sign in again to access your dashboard.</p>
      <div class="modal-buttons" style="justify-content: center;">
        <button class="modal-btn modal-btn-cancel" onclick="closeLogoutModal()">Cancel</button>
        <button class="modal-btn modal-btn-logout" onclick="confirmLogout()" style="background: #ef4444; color: white;">Yes, Logout</button>
      </div>
    </div>
  `;
  document.body.appendChild(overlay);
}

function closeLogoutModal() {
  const modal = document.getElementById('logoutModal');
  if (modal) modal.remove();
}

async function confirmLogout() {
  closeLogoutModal();
  try {
    await fetch('/logout');
    sessionStorage.clear();
    localStorage.removeItem('rememberedEmail');
    localStorage.removeItem('email');
    localStorage.removeItem('jwt_token');
    localStorage.removeItem('role');
    sessionStorage.removeItem('role');
    window.location.href = '/';
  } catch (error) {
    console.error('Logout error:', error);
    window.location.href = '/';
  }
}

// ── Close modals on ESC ─────────────────────────────────────────────
document.addEventListener('keydown', function(e) {
  if (e.key === 'Escape') {
    closeBookAppointmentModal();
    closeEditPetImageModal();
    closeLogoutModal();
  }
});

// ── Click outside modal to close ──────────────────────────────────
document.addEventListener('click', function(e) {
  if (e.target.classList.contains('modal-overlay')) {
    closeBookAppointmentModal();
    closeEditPetImageModal();
    closeLogoutModal();
  }
});

// ── Initialize ──────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', function() {
  loadMyPets();
  loadAppointments();
});

// ── Also reload when coming back to page ──────────────────────────
window.addEventListener('pageshow', function() {
  loadMyPets();
  loadAppointments();
});