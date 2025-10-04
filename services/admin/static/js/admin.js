// Admin Panel JavaScript

const API_BASE = window.location.origin;
let authToken = localStorage.getItem('adminToken');
let currentAdmin = null;
let currentPage = 1;
let currentSection = 'dashboard';

// Initialize app
document.addEventListener('DOMContentLoaded', () => {
    if (authToken) {
        showDashboard();
        loadStats();
    } else {
        showLogin();
    }
    
    setupEventListeners();
});

function setupEventListeners() {
    // Login form
    document.getElementById('loginForm').addEventListener('submit', handleLogin);
    
    // Logout
    document.getElementById('logoutBtn').addEventListener('click', handleLogout);
    
    // Navigation
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const section = e.target.dataset.section;
            if (section) {
                switchSection(section);
            }
        });
    });
    
    // User search
    document.getElementById('searchUsersBtn')?.addEventListener('click', () => {
        loadUsers(1);
    });
    
    document.getElementById('userSearch')?.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            loadUsers(1);
        }
    });
    
    // Photo filters
    document.querySelectorAll('input[name="photoFilter"]').forEach(radio => {
        radio.addEventListener('change', () => {
            loadPhotos(1);
        });
    });
    
    // Close modal
    document.querySelectorAll('.close').forEach(closeBtn => {
        closeBtn.addEventListener('click', () => {
            closeBtn.closest('.modal').classList.add('hidden');
        });
    });
}

function showLogin() {
    document.getElementById('loginScreen').classList.remove('hidden');
    document.getElementById('dashboardScreen').classList.add('hidden');
}

function showDashboard() {
    document.getElementById('loginScreen').classList.add('hidden');
    document.getElementById('dashboardScreen').classList.remove('hidden');
}

async function handleLogin(e) {
    e.preventDefault();
    
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const errorDiv = document.getElementById('loginError');
    
    errorDiv.classList.add('hidden');
    
    try {
        const response = await fetch(`${API_BASE}/admin/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            authToken = data.token;
            currentAdmin = data.admin;
            localStorage.setItem('adminToken', authToken);
            localStorage.setItem('adminInfo', JSON.stringify(currentAdmin));
            
            document.getElementById('adminName').textContent = currentAdmin.full_name || currentAdmin.username;
            
            showDashboard();
            loadStats();
        } else {
            errorDiv.textContent = data.error || 'Ошибка входа';
            errorDiv.classList.remove('hidden');
        }
    } catch (error) {
        console.error('Login error:', error);
        errorDiv.textContent = 'Ошибка подключения к серверу';
        errorDiv.classList.remove('hidden');
    }
}

function handleLogout() {
    authToken = null;
    currentAdmin = null;
    localStorage.removeItem('adminToken');
    localStorage.removeItem('adminInfo');
    showLogin();
}

function switchSection(section) {
    currentSection = section;
    
    // Update navigation
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('active');
    });
    document.querySelector(`[data-section="${section}"]`).classList.add('active');
    
    // Show section
    document.querySelectorAll('.content-section').forEach(sec => {
        sec.classList.add('hidden');
    });
    document.getElementById(section).classList.remove('hidden');
    
    // Load section data
    switch(section) {
        case 'dashboard':
            loadStats();
            break;
        case 'users':
            loadUsers(1);
            break;
        case 'photos':
            loadPhotos(1);
            break;
    }
}

async function loadStats() {
    try {
        const response = await fetch(`${API_BASE}/admin/stats`, {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        
        if (response.ok) {
            const stats = await response.json();
            
            document.getElementById('totalUsers').textContent = stats.users.total;
            document.getElementById('activeUsers').textContent = stats.users.active;
            document.getElementById('bannedUsers').textContent = stats.users.banned;
            document.getElementById('completeProfiles').textContent = stats.profiles.complete;
            document.getElementById('totalPhotos').textContent = stats.photos.total;
            document.getElementById('pendingPhotos').textContent = stats.photos.pending;
            document.getElementById('totalMatches').textContent = stats.matches;
            document.getElementById('totalInteractions').textContent = stats.interactions;
        }
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

async function loadUsers(page = 1) {
    const search = document.getElementById('userSearch').value;
    
    try {
        const params = new URLSearchParams({
            page: page,
            per_page: 20,
            search: search
        });
        
        const response = await fetch(`${API_BASE}/admin/users?${params}`, {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        
        if (response.ok) {
            const data = await response.json();
            renderUsersTable(data.users);
            renderPagination(data, 'usersPagination', loadUsers);
        }
    } catch (error) {
        console.error('Error loading users:', error);
    }
}

function renderUsersTable(users) {
    const container = document.getElementById('usersTable');
    
    if (users.length === 0) {
        container.innerHTML = '<p>Пользователи не найдены</p>';
        return;
    }
    
    let html = '<div class="table"><table>';
    html += '<thead><tr>';
    html += '<th>ID</th>';
    html += '<th>Username</th>';
    html += '<th>Имя</th>';
    html += '<th>Premium</th>';
    html += '<th>Статус</th>';
    html += '<th>Создан</th>';
    html += '<th>Действия</th>';
    html += '</tr></thead><tbody>';
    
    users.forEach(user => {
        html += '<tr>';
        html += `<td>${user.id}</td>`;
        html += `<td>@${user.username || '-'}</td>`;
        html += `<td>${user.first_name || '-'}</td>`;
        html += `<td>${user.is_premium ? '⭐' : ''}</td>`;
        html += `<td>`;
        if (user.is_banned) {
            html += '<span class="badge badge-danger">Заблокирован</span>';
        } else {
            html += '<span class="badge badge-success">Активен</span>';
        }
        html += `</td>`;
        html += `<td>${new Date(user.created_at).toLocaleDateString()}</td>`;
        html += `<td>`;
        html += `<button class="btn btn-small btn-primary" onclick="viewUser(${user.id})">Просмотр</button>`;
        html += `</td>`;
        html += '</tr>';
    });
    
    html += '</tbody></table></div>';
    container.innerHTML = html;
}

async function viewUser(userId) {
    try {
        const response = await fetch(`${API_BASE}/admin/users/${userId}`, {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        
        if (response.ok) {
            const user = await response.json();
            renderUserDetails(user);
            document.getElementById('userModal').classList.remove('hidden');
        }
    } catch (error) {
        console.error('Error loading user:', error);
    }
}

function renderUserDetails(user) {
    const container = document.getElementById('userDetails');
    
    let html = '<div class="user-detail-section">';
    html += '<h3>Информация о пользователе</h3>';
    html += '<div class="user-detail-grid">';
    html += `<div class="user-detail-item"><strong>ID</strong>${user.id}</div>`;
    html += `<div class="user-detail-item"><strong>Telegram ID</strong>${user.tg_id}</div>`;
    html += `<div class="user-detail-item"><strong>Username</strong>@${user.username || '-'}</div>`;
    html += `<div class="user-detail-item"><strong>Имя</strong>${user.first_name || '-'}</div>`;
    html += `<div class="user-detail-item"><strong>Premium</strong>${user.is_premium ? 'Да' : 'Нет'}</div>`;
    html += `<div class="user-detail-item"><strong>Статус</strong>${user.is_banned ? 'Заблокирован' : 'Активен'}</div>`;
    html += `<div class="user-detail-item"><strong>Создан</strong>${new Date(user.created_at).toLocaleString()}</div>`;
    html += `<div class="user-detail-item"><strong>Обновлен</strong>${new Date(user.updated_at).toLocaleString()}</div>`;
    html += '</div></div>';
    
    if (user.stats) {
        html += '<div class="user-detail-section">';
        html += '<h3>Статистика</h3>';
        html += '<div class="user-detail-grid">';
        html += `<div class="user-detail-item"><strong>Лайков отправлено</strong>${user.stats.likes_given}</div>`;
        html += `<div class="user-detail-item"><strong>Лайков получено</strong>${user.stats.likes_received}</div>`;
        html += `<div class="user-detail-item"><strong>Матчей</strong>${user.stats.matches}</div>`;
        html += '</div></div>';
    }
    
    if (user.profile) {
        html += '<div class="user-detail-section">';
        html += '<h3>Профиль</h3>';
        html += '<div class="user-detail-grid">';
        html += `<div class="user-detail-item"><strong>Имя</strong>${user.profile.name}</div>`;
        html += `<div class="user-detail-item"><strong>Возраст</strong>${calculateAge(user.profile.birth_date)} лет</div>`;
        html += `<div class="user-detail-item"><strong>Пол</strong>${translateGender(user.profile.gender)}</div>`;
        html += `<div class="user-detail-item"><strong>Город</strong>${user.profile.city || '-'}</div>`;
        html += `<div class="user-detail-item"><strong>Цель</strong>${translateGoal(user.profile.goal)}</div>`;
        html += `<div class="user-detail-item"><strong>Образование</strong>${translateEducation(user.profile.education)}</div>`;
        html += '</div>';
        if (user.profile.bio) {
            html += `<p style="margin-top: 15px;"><strong>О себе:</strong> ${user.profile.bio}</p>`;
        }
        html += '</div>';
    }
    
    if (user.photos && user.photos.length > 0) {
        html += '<div class="user-detail-section">';
        html += '<h3>Фотографии</h3>';
        html += '<div class="user-photos">';
        user.photos.forEach(photo => {
            html += `<div>`;
            html += `<img src="${photo.url}" alt="Photo">`;
            html += `<p style="font-size: 11px; margin-top: 5px;">`;
            html += photo.is_verified ? '✅ Проверено' : '⏳ На проверке';
            html += `<br>Safe score: ${photo.safe_score.toFixed(2)}`;
            html += `</p></div>`;
        });
        html += '</div></div>';
    }
    
    html += '<div class="user-detail-section">';
    html += '<h3>Действия</h3>';
    html += '<div style="display: flex; gap: 10px;">';
    if (user.is_banned) {
        html += `<button class="btn btn-success" onclick="toggleBan(${user.id}, false)">Разблокировать</button>`;
    } else {
        html += `<button class="btn btn-danger" onclick="toggleBan(${user.id}, true)">Заблокировать</button>`;
    }
    html += '</div></div>';
    
    container.innerHTML = html;
}

async function toggleBan(userId, ban) {
    try {
        const response = await fetch(`${API_BASE}/admin/users/${userId}`, {
            method: 'PUT',
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ is_banned: ban })
        });
        
        if (response.ok) {
            document.getElementById('userModal').classList.add('hidden');
            loadUsers(currentPage);
            alert(ban ? 'Пользователь заблокирован' : 'Пользователь разблокирован');
        }
    } catch (error) {
        console.error('Error toggling ban:', error);
        alert('Ошибка при изменении статуса пользователя');
    }
}

async function loadPhotos(page = 1) {
    const filter = document.querySelector('input[name="photoFilter"]:checked').value;
    
    try {
        const params = new URLSearchParams({
            page: page,
            per_page: 20
        });
        
        if (filter === 'verified') {
            params.append('verified', 'true');
        } else if (filter === 'unverified') {
            params.append('unverified', 'true');
        }
        
        const response = await fetch(`${API_BASE}/admin/photos?${params}`, {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        
        if (response.ok) {
            const data = await response.json();
            renderPhotosGrid(data.photos);
            renderPagination(data, 'photosPagination', loadPhotos);
        }
    } catch (error) {
        console.error('Error loading photos:', error);
    }
}

function renderPhotosGrid(photos) {
    const container = document.getElementById('photosGrid');
    
    if (photos.length === 0) {
        container.innerHTML = '<p>Фотографии не найдены</p>';
        return;
    }
    
    container.innerHTML = photos.map(photo => `
        <div class="photo-card">
            <img src="${photo.url}" alt="Photo">
            <div class="photo-card-info">
                <p><strong>User ID:</strong> ${photo.user_id}</p>
                <p><strong>Safe score:</strong> ${photo.safe_score.toFixed(2)}</p>
                <p><strong>Статус:</strong> ${photo.is_verified ? '✅ Проверено' : '⏳ На проверке'}</p>
                <p><strong>Загружено:</strong> ${new Date(photo.created_at).toLocaleDateString()}</p>
                <div class="photo-card-actions">
                    ${!photo.is_verified ? `<button class="btn btn-small btn-success" onclick="approvePhoto(${photo.id})">Одобрить</button>` : ''}
                    <button class="btn btn-small btn-danger" onclick="deletePhoto(${photo.id})">Удалить</button>
                </div>
            </div>
        </div>
    `).join('');
}

async function approvePhoto(photoId) {
    try {
        const response = await fetch(`${API_BASE}/admin/photos/${photoId}`, {
            method: 'PUT',
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ is_verified: true })
        });
        
        if (response.ok) {
            loadPhotos(currentPage);
            loadStats();
        }
    } catch (error) {
        console.error('Error approving photo:', error);
    }
}

async function deletePhoto(photoId) {
    if (!confirm('Удалить это фото?')) return;
    
    try {
        const response = await fetch(`${API_BASE}/admin/photos/${photoId}`, {
            method: 'DELETE',
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        
        if (response.ok) {
            loadPhotos(currentPage);
            loadStats();
        }
    } catch (error) {
        console.error('Error deleting photo:', error);
    }
}

function renderPagination(data, containerId, loadFunction) {
    const container = document.getElementById(containerId);
    
    if (data.pages <= 1) {
        container.innerHTML = '';
        return;
    }
    
    let html = '';
    
    if (data.page > 1) {
        html += `<button onclick="${loadFunction.name}(${data.page - 1})">Предыдущая</button>`;
    }
    
    for (let i = 1; i <= data.pages; i++) {
        if (i === 1 || i === data.pages || (i >= data.page - 2 && i <= data.page + 2)) {
            html += `<button class="${i === data.page ? 'active' : ''}" onclick="${loadFunction.name}(${i})">${i}</button>`;
        } else if (i === data.page - 3 || i === data.page + 3) {
            html += '<span>...</span>';
        }
    }
    
    if (data.page < data.pages) {
        html += `<button onclick="${loadFunction.name}(${data.page + 1})">Следующая</button>`;
    }
    
    container.innerHTML = html;
}

// Helper functions
function calculateAge(birthDate) {
    const today = new Date();
    const birth = new Date(birthDate);
    let age = today.getFullYear() - birth.getFullYear();
    const monthDiff = today.getMonth() - birth.getMonth();
    if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birth.getDate())) {
        age--;
    }
    return age;
}

function translateGender(gender) {
    const map = {
        'male': 'Мужской',
        'female': 'Женский',
        'other': 'Другой'
    };
    return map[gender] || gender;
}

function translateGoal(goal) {
    const map = {
        'friendship': 'Дружба',
        'dating': 'Знакомства',
        'relationship': 'Отношения',
        'networking': 'Нетворкинг',
        'serious': 'Серьезные отношения',
        'casual': 'Легкие знакомства'
    };
    return map[goal] || goal;
}

function translateEducation(education) {
    const map = {
        'high_school': 'Среднее',
        'bachelor': 'Бакалавр',
        'master': 'Магистр',
        'phd': 'PhD',
        'other': 'Другое'
    };
    return map[education] || education || '-';
}
