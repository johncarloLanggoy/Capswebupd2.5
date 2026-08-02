// ── Tab Navigation ───────────────────────────────────────────────────
function showPetsTab() {
    document.getElementById('customerSection').style.display = 'none';
    document.getElementById('petSection').style.display = 'block';
    document.getElementById('appointmentsSection').style.display = 'none';
    document.getElementById('navCustomers').classList.remove('active');
    document.getElementById('navPets').classList.add('active');
    document.getElementById('navAppointments').classList.remove('active');
    loadPets();
}

function showCustomersTab() {
    document.getElementById('customerSection').style.display = 'block';
    document.getElementById('petSection').style.display = 'none';
    document.getElementById('appointmentsSection').style.display = 'none';
    document.getElementById('navPets').classList.remove('active');
    document.getElementById('navAppointments').classList.remove('active');
    document.getElementById('navCustomers').classList.add('active');
}

function showAppointmentsTab() {
    document.getElementById('customerSection').style.display = 'none';
    document.getElementById('petSection').style.display = 'none';
    document.getElementById('appointmentsSection').style.display = 'block';
    document.getElementById('navCustomers').classList.remove('active');
    document.getElementById('navPets').classList.remove('active');
    document.getElementById('navAppointments').classList.add('active');
    loadAllAppointments();
}

// ── Show/Hide Messages ─────────────────────────────────────────────
function showMessage(text, type) {
    const msg = document.getElementById('message');
    msg.textContent = text;
    msg.style.backgroundColor = type === 'success' ? '#10b981' : '#ef4444';
    msg.style.display = 'block';
    setTimeout(() => {
        msg.style.display = 'none';
    }, 4000);
}

// ── Load Customers for Dropdown ────────────────────────────────────
async function loadCustomers() {
    try {
        const res = await fetch('/api/customers');
        const data = await res.json();
        if (data.success) {
            const select = document.getElementById('petOwner');
            select.innerHTML = '<option value="">Select customer...</option>';
            data.customers.forEach(customer => {
                const option = document.createElement('option');
                option.value = customer.email;
                option.textContent = customer.email;
                select.appendChild(option);
            });
        }
    } catch (error) {
        console.error('Error loading customers:', error);
    }
}

// ── Pet Image Preview ──────────────────────────────────────────────────
function previewPetImage(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    const reader = new FileReader();
    reader.onload = function(e) {
        const preview = document.getElementById('petImagePreview');
        preview.innerHTML = `<img src="${e.target.result}" style="width: 100%; height: 100%; object-fit: cover;">`;
    };
    reader.readAsDataURL(file);
}

function previewEditPetImage(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    const reader = new FileReader();
    reader.onload = function(e) {
        const preview = document.getElementById('editPetImagePreview');
        preview.innerHTML = `<img src="${e.target.result}" style="width: 100%; height: 100%; object-fit: cover;">`;
    };
    reader.readAsDataURL(file);
}

// ── Get base64 image from file input ──────────────────────────────────
function getBase64Image(fileInput) {
    return new Promise((resolve) => {
        const file = fileInput.files[0];
        if (!file) {
            resolve('');
            return;
        }
        const reader = new FileReader();
        reader.onload = function(e) {
            resolve(e.target.result);
        };
        reader.readAsDataURL(file);
    });
}

// ── Load Pets ───────────────────────────────────────────────────────
async function loadPets() {
    try {
        const res = await fetch('/api/pets');
        const data = await res.json();
        const tbody = document.getElementById('petTableBody');
        
        if (data.success && data.pets.length > 0) {
            tbody.innerHTML = '';
            data.pets.forEach(pet => {
                const statusClass = pet.medical_history ? 'pet-status-warning' : 'pet-status-healthy';
                const statusText = pet.medical_history ? '⚠️ Attention' : '✅ Healthy';
                
                // Determine pet type and icon
                const petType = pet.pet_type || 'Dog';
                const petIcon = petType === 'Cat' ? '🐈' : '🐕';
                const petTypeLabel = petType === 'Cat' ? 'Cat' : 'Dog';
                
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${pet.id}</td>
                    <td>
                        <div style="display: flex; align-items: center; gap: 10px;">
                            ${pet.pet_image ? 
                                `<img src="${pet.pet_image}" style="width: 35px; height: 35px; border-radius: 50%; object-fit: cover;">` : 
                                `<span style="font-size: 24px;">${petIcon}</span>`
                            }
                            <strong>${pet.name}</strong>
                        </div>
                    </td>
                    <td>${petTypeLabel}</td>
                    <td>${pet.breed || '—'}</td>
                    <td>${pet.age || '—'}</td>
                    <td>${pet.gender || '—'}</td>
                    <td><span class="truncate" title="${pet.owner_email}">${pet.owner_email}</span></td>
                    <td><span class="pet-status ${statusClass}">${statusText}</span></td>
                    <td>
                        <div class="action-buttons">
                            <button class="btn-edit" onclick="showEditPetModal(${pet.id})">✏️ Edit</button>
                            <button class="btn-delete" onclick="deletePet(${pet.id})">🗑️ Delete</button>
                        </div>
                    </td>
                `;
                tbody.appendChild(row);
            });
        } else {
            tbody.innerHTML = `
                <tr>
                    <td colspan="9" style="text-align: center; color: #64748b; padding: 30px;">
                        No pets registered yet. Click "Register Pet" to add one.
                    </td>
                </tr>
            `;
        }
    } catch (error) {
        console.error('Error loading pets:', error);
    }
}

// ── Load All Appointments ──────────────────────────────────────────
async function loadAllAppointments() {
    try {
        const res = await fetch('/api/appointments/all');
        const data = await res.json();
        const tbody = document.getElementById('appointmentsTableBody');
        
        if (data.success && data.appointments.length > 0) {
            document.getElementById('totalAppointments').textContent = data.appointments.length;
            const pending = data.appointments.filter(a => a.status === 'pending').length;
            document.getElementById('pendingAppointments').textContent = pending;
            
            tbody.innerHTML = '';
            data.appointments.forEach(app => {
                const statusClass = `status-${app.status}`;
                const statusLabel = app.status.charAt(0).toUpperCase() + app.status.slice(1);
                
                let actionsHTML = '';
                if (app.status === 'pending') {
                    actionsHTML = `
                        <button class="btn-confirm" onclick="updateAppointmentStatus(${app.id}, 'confirmed')">Confirm</button>
                        <button class="btn-cancel" onclick="updateAppointmentStatus(${app.id}, 'cancelled')">Cancel</button>
                    `;
                } else if (app.status === 'confirmed') {
                    actionsHTML = `
                        <button class="btn-complete" onclick="updateAppointmentStatus(${app.id}, 'completed')">Complete</button>
                        <button class="btn-cancel" onclick="updateAppointmentStatus(${app.id}, 'cancelled')">Cancel</button>
                    `;
                } else {
                    actionsHTML = `<span style="color: #64748b; font-size: 11px;">No actions</span>`;
                }
                
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${app.id}</td>
                    <td>${app.pet_name}</td>
                    <td><span class="truncate" title="${app.customer_email}">${app.customer_email}</span></td>
                    <td>${app.service_name}</td>
                    <td>${app.appointment_date}</td>
                    <td>${app.appointment_time}</td>
                    <td><span class="pet-status ${statusClass}">${statusLabel}</span></td>
                    <td>
                        <div class="action-buttons">
                            ${actionsHTML}
                        </div>
                    </td>
                `;
                tbody.appendChild(row);
            });
        } else {
            document.getElementById('totalAppointments').textContent = '0';
            document.getElementById('pendingAppointments').textContent = '0';
            tbody.innerHTML = `
                <tr>
                    <td colspan="8" style="text-align: center; color: #64748b; padding: 30px;">
                        No appointments booked yet.
                    </td>
                </tr>
            `;
        }
    } catch (error) {
        console.error('Error loading appointments:', error);
    }
}

// ── Update Appointment Status ──────────────────────────────────────
async function updateAppointmentStatus(appointmentId, status) {
    if (!confirm(`Are you sure you want to mark this appointment as ${status}?`)) return;
    
    try {
        const res = await fetch(`/api/appointments/${appointmentId}/status`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status })
        });
        const data = await res.json();
        
        if (data.success) {
            showMessage(`Appointment ${status}! ✅`, 'success');
            loadAllAppointments();
        } else {
            showMessage(data.message || 'Error updating appointment.', 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showMessage('Something went wrong. Please try again.', 'error');
    }
}

// ── Add Pet Modal ──────────────────────────────────────────────────
function showAddPetModal() {
    document.getElementById('addPetModal').style.display = 'flex';
    loadCustomers();
    document.getElementById('petForm').reset();
    document.getElementById('petImagePreview').innerHTML = '<span style="color: #64748b; font-size: 12px; text-align: center;">No<br>Image</span>';
}

function closeAddPetModal() {
    document.getElementById('addPetModal').style.display = 'none';
}

async function submitPet(e) {
    e.preventDefault();
    
    const customer_email = document.getElementById('petOwner').value;
    const pet_type = document.getElementById('petType').value;
    const name = document.getElementById('petName').value.trim();
    const breed = document.getElementById('petBreed').value.trim();
    const age = document.getElementById('petAge').value;
    const gender = document.getElementById('petGender').value;
    const color = document.getElementById('petColor').value.trim();
    const weight = document.getElementById('petWeight').value;
    const allergies = document.getElementById('petAllergies').value.trim();
    const medical_history = document.getElementById('petMedicalHistory').value.trim();
    
    // Get image as base64
    const imageInput = document.getElementById('petImage');
    let pet_image = '';
    if (imageInput && imageInput.files && imageInput.files[0]) {
        pet_image = await getBase64Image(imageInput);
    }
    
    if (!customer_email) {
        showMessage('Please select a customer.', 'error');
        return;
    }
    if (!name) {
        showMessage('Please enter pet name.', 'error');
        return;
    }
    
    try {
        const res = await fetch('/api/pets', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                customer_email, pet_type, name, breed, age, gender, color, weight, allergies, medical_history, pet_image
            })
        });
        const data = await res.json();
        
        if (data.success) {
            showMessage('Pet registered successfully! 🎉', 'success');
            closeAddPetModal();
            loadPets();
            const totalPetsEl = document.getElementById('totalPets');
            if (totalPetsEl) {
                const current = parseInt(totalPetsEl.textContent) || 0;
                totalPetsEl.textContent = current + 1;
            }
        } else {
            showMessage(data.message || 'Error registering pet.', 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showMessage('Something went wrong. Please try again.', 'error');
    }
}

// ── Edit Pet Modal ──────────────────────────────────────────────────
async function showEditPetModal(petId) {
    document.getElementById('editPetModal').style.display = 'flex';
    
    try {
        const res = await fetch('/api/pets');
        const data = await res.json();
        if (data.success) {
            const pet = data.pets.find(p => p.id === petId);
            if (pet) {
                document.getElementById('editPetId').value = pet.id;
                document.getElementById('editPetType').value = pet.pet_type || 'Dog';
                document.getElementById('editPetName').value = pet.name || '';
                document.getElementById('editPetBreed').value = pet.breed || '';
                document.getElementById('editPetAge').value = pet.age || '';
                document.getElementById('editPetGender').value = pet.gender || '';
                document.getElementById('editPetColor').value = pet.color || '';
                document.getElementById('editPetWeight').value = pet.weight || '';
                document.getElementById('editPetAllergies').value = pet.allergies || '';
                document.getElementById('editPetMedicalHistory').value = pet.medical_history || '';
                
                // Show existing image if any
                const preview = document.getElementById('editPetImagePreview');
                if (pet.pet_image) {
                    preview.innerHTML = `<img src="${pet.pet_image}" style="width: 100%; height: 100%; object-fit: cover;">`;
                } else {
                    preview.innerHTML = `<span style="color: #64748b; font-size: 12px; text-align: center;">No<br>Image</span>`;
                }
            }
        }
    } catch (error) {
        console.error('Error loading pet details:', error);
    }
}

function closeEditPetModal() {
    document.getElementById('editPetModal').style.display = 'none';
}

async function updatePet(e) {
    e.preventDefault();
    
    const petId = document.getElementById('editPetId').value;
    const pet_type = document.getElementById('editPetType').value;
    const name = document.getElementById('editPetName').value.trim();
    const breed = document.getElementById('editPetBreed').value.trim();
    const age = document.getElementById('editPetAge').value;
    const gender = document.getElementById('editPetGender').value;
    const color = document.getElementById('editPetColor').value.trim();
    const weight = document.getElementById('editPetWeight').value;
    const allergies = document.getElementById('editPetAllergies').value.trim();
    const medical_history = document.getElementById('editPetMedicalHistory').value.trim();
    
    // Get image as base64
    const imageInput = document.getElementById('editPetImage');
    let pet_image = '';
    if (imageInput && imageInput.files && imageInput.files[0]) {
        pet_image = await getBase64Image(imageInput);
    }
    
    if (!name) {
        showMessage('Please enter pet name.', 'error');
        return;
    }
    
    try {
        const res = await fetch(`/api/pets/${petId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ pet_type, name, breed, age, gender, color, weight, allergies, medical_history, pet_image })
        });
        const data = await res.json();
        
        if (data.success) {
            showMessage('Pet updated successfully! ✅', 'success');
            closeEditPetModal();
            loadPets();
        } else {
            showMessage(data.message || 'Error updating pet.', 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showMessage('Something went wrong. Please try again.', 'error');
    }
}

// ── Delete Pet ──────────────────────────────────────────────────────
async function deletePet(petId) {
    if (!confirm('Are you sure you want to delete this pet? This action cannot be undone.')) {
        return;
    }
    
    try {
        const res = await fetch(`/api/pets/${petId}`, {
            method: 'DELETE'
        });
        const data = await res.json();
        
        if (data.success) {
            showMessage('Pet deleted successfully! 🗑️', 'success');
            loadPets();
            const totalPetsEl = document.getElementById('totalPets');
            if (totalPetsEl) {
                const current = parseInt(totalPetsEl.textContent) || 0;
                totalPetsEl.textContent = current > 0 ? current - 1 : 0;
            }
        } else {
            showMessage(data.message || 'Error deleting pet.', 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showMessage('Something went wrong. Please try again.', 'error');
    }
}

// ── Logout ──────────────────────────────────────────────────────────
function showLogoutModal() {
    document.getElementById('logoutModal').style.display = 'flex';
}

function closeLogoutModal() {
    document.getElementById('logoutModal').style.display = 'none';
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

// ── Close modals on ESC key ──────────────────────────────────────
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        closeAddPetModal();
        closeEditPetModal();
        closeLogoutModal();
    }
});

// ── Click outside modal to close ──────────────────────────────────
document.addEventListener('click', function(e) {
    if (e.target.classList.contains('modal-overlay')) {
        closeAddPetModal();
        closeEditPetModal();
        closeLogoutModal();
    }
});