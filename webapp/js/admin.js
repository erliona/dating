// Admin Panel using Telegram WebApp API
class AdminPanel {
    constructor() {
        this.tg = window.Telegram.WebApp;
        this.currentScreen = 'login';
        this.currentSection = 'dashboard';
        this.admin = null;
        this.stats = {};
        this.users = [];
        this.photos = [];
        this.currentPage = 1;
        this.itemsPerPage = 20;
        
        this.init();
    }

    init() {
        // Initialize Telegram WebApp
        this.tg.ready();
        this.tg.expand();
        
        // Set up theme
        this.setupTheme();
        
        // Set up navigation
        this.setupNavigation();
        
        // Set up event listeners
        this.setupEventListeners();
        
        // Check if already logged in
        this.checkAuth();
    }

    setupTheme() {
        // Apply Telegram theme colors
        const root = document.documentElement;
        const theme = this.tg.themeParams;
        
        if (theme.bg_color) {
            root.style.setProperty('--tg-theme-bg-color', theme.bg_color);
        }
        if (theme.text_color) {
            root.style.setProperty('--tg-theme-text-color', theme.text_color);
        }
        if (theme.hint_color) {
            root.style.setProperty('--tg-theme-hint-color', theme.hint_color);
        }
        if (theme.link_color) {
            root.style.setProperty('--tg-theme-link-color', theme.link_color);
        }
        if (theme.button_color) {
            root.style.setProperty('--tg-theme-button-color', theme.button_color);
        }
        if (theme.button_text_color) {
            root.style.setProperty('--tg-theme-button-text-color', theme.button_text_color);
        }
        if (theme.secondary_bg_color) {
            root.style.setProperty('--tg-theme-secondary-bg-color', theme.secondary_bg_color);
        }
    }

    setupNavigation() {
        // Set up Telegram WebApp navigation
        this.tg.BackButton.hide();
        this.tg.MainButton.hide();
        
        // Handle back button
        this.tg.BackButton.onClick(() => {
            this.handleBackButton();
        });
    }

    setupEventListeners() {
        // Login form
        document.getElementById('loginForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleLogin();
        });

        // Logout button
        document.getElementById('logoutBtn').addEventListener('click', () => {
            this.handleLogout();
        });

        // Navigation
        document.querySelectorAll('.nav-item').forEach(item => {
            item.addEventListener('click', (e) => {
                const section = e.target.dataset.section;
                this.showSection(section);
            });
        });

        // User search
        document.getElementById('searchUsersBtn').addEventListener('click', () => {
            this.searchUsers();
        });

        // Photo filters
        document.querySelectorAll('input[name="photoFilter"]').forEach(radio => {
            radio.addEventListener('change', (e) => {
                this.filterPhotos(e.target.value);
            });
        });

        // Create admin form
        document.getElementById('createAdminForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.createAdmin();
        });

        // Modal close
        document.querySelector('.close').addEventListener('click', () => {
            this.closeModal();
        });

        // Click outside modal to close
        document.getElementById('userModal').addEventListener('click', (e) => {
            if (e.target.id === 'userModal') {
                this.closeModal();
            }
        });
    }

    async checkAuth() {
        try {
            const token = localStorage.getItem('adminToken');
            if (token) {
                const response = await fetch('/api/admin/me', {
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                });
                
                if (response.ok) {
                    this.admin = await response.json();
                    this.showScreen('dashboard');
                    this.loadDashboard();
                } else {
                    localStorage.removeItem('adminToken');
                    this.showScreen('login');
                }
            } else {
                this.showScreen('login');
            }
        } catch (error) {
            console.error('Auth check error:', error);
            this.showScreen('login');
        }
    }

    async handleLogin() {
        try {
            const formData = new FormData(document.getElementById('loginForm'));
            const credentials = Object.fromEntries(formData.entries());
            
            const response = await fetch('/api/admin/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(credentials)
            });

            if (response.ok) {
                const data = await response.json();
                localStorage.setItem('adminToken', data.token);
                this.admin = data.admin;
                this.showScreen('dashboard');
                this.loadDashboard();
                this.tg.showAlert('Вход выполнен успешно!');
            } else {
                const error = await response.json();
                this.showError(error.message);
            }
        } catch (error) {
            console.error('Login error:', error);
            this.showError('Ошибка входа в систему');
        }
    }

    handleLogout() {
        localStorage.removeItem('adminToken');
        this.admin = null;
        this.showScreen('login');
        this.tg.showAlert('Вы вышли из системы');
    }

    showScreen(screenName) {
        // Hide all screens
        document.querySelectorAll('.screen').forEach(screen => {
            screen.classList.add('hidden');
        });
        
        // Show target screen
        document.getElementById(`${screenName}Screen`).classList.remove('hidden');
        this.currentScreen = screenName;
        
        // Update navigation
        this.updateNavigation();
    }

    showSection(sectionName) {
        // Hide all sections
        document.querySelectorAll('.content-section').forEach(section => {
            section.classList.add('hidden');
        });
        
        // Show target section
        document.getElementById(sectionName).classList.remove('hidden');
        this.currentSection = sectionName;
        
        // Update navigation
        document.querySelectorAll('.nav-item').forEach(item => {
            item.classList.remove('active');
        });
        document.querySelector(`[data-section="${sectionName}"]`).classList.add('active');
        
        // Load section data
        this.loadSectionData(sectionName);
    }

    loadSectionData(sectionName) {
        switch (sectionName) {
            case 'dashboard':
                this.loadDashboard();
                break;
            case 'users':
                this.loadUsers();
                break;
            case 'photos':
                this.loadPhotos();
                break;
            case 'settings':
                this.loadSettings();
                break;
        }
    }

    async loadDashboard() {
        try {
            const response = await fetch('/api/admin/stats', {
                headers: {
                    'Authorization': `Bearer ${this.getAuthToken()}`
                }
            });

            if (response.ok) {
                this.stats = await response.json();
                this.updateStatsDisplay();
            }
    }

    updateStatsDisplay() {
        document.getElementById('totalUsers').textContent = this.stats.totalUsers || 0;
        document.getElementById('activeUsers').textContent = this.stats.activeUsers || 0;
        document.getElementById('completeProfiles').textContent = this.stats.completeProfiles || 0;
        document.getElementById('totalPhotos').textContent = this.stats.totalPhotos || 0;
        document.getElementById('pendingPhotos').textContent = this.stats.pendingPhotos || 0;
        document.getElementById('totalMatches').textContent = this.stats.totalMatches || 0;
        document.getElementById('totalInteractions').textContent = this.stats.totalInteractions || 0;
        document.getElementById('bannedUsers').textContent = this.stats.bannedUsers || 0;
    }

    async loadUsers() {
        try {
            const response = await fetch(`/api/admin/users?page=${this.currentPage}&limit=${this.itemsPerPage}`, {
                headers: {
                    'Authorization': `Bearer ${this.getAuthToken()}`
                }
            });

            if (response.ok) {
                const data = await response.json();
                this.users = data.users;
                this.updateUsersDisplay();
                this.updatePagination('users', data.total, data.page, data.pages);
            }
        } catch (error) {
            console.error('Error loading users:', error);
        }
    }

    updateUsersDisplay() {
        const usersTable = document.getElementById('usersTable');
        usersTable.innerHTML = '';

        this.users.forEach(user => {
            const userRow = document.createElement('div');
            userRow.className = 'user-row';
            userRow.innerHTML = `
                <img src="${user.avatar || '/images/default-avatar.png'}" alt="${user.name}" class="user-avatar">
                <div class="user-info">
                    <div class="user-name">${user.name}</div>
                    <div class="user-username">@${user.username || 'no_username'}</div>
                </div>
                <div class="user-status ${user.status}">${user.status === 'active' ? 'Активен' : 'Забанен'}</div>
                <div class="user-actions">
                    <button class="btn btn-small btn-secondary" onclick="adminPanel.viewUser(${user.id})">Просмотр</button>
                    <button class="btn btn-small ${user.status === 'active' ? 'btn-danger' : 'btn-success'}" onclick="adminPanel.toggleUserStatus(${user.id})">
                        ${user.status === 'active' ? 'Забанить' : 'Разбанить'}
                    </button>
                </div>
            `;
            usersTable.appendChild(userRow);
        });
    }

    async loadPhotos() {
        try {
            const filter = document.querySelector('input[name="photoFilter"]:checked').value;
            const response = await fetch(`/api/admin/photos?filter=${filter}&page=${this.currentPage}&limit=${this.itemsPerPage}`, {
                headers: {
                    'Authorization': `Bearer ${this.getAuthToken()}`
                }
            });

            if (response.ok) {
                const data = await response.json();
                this.photos = data.photos;
                this.updatePhotosDisplay();
                this.updatePagination('photos', data.total, data.page, data.pages);
            }
        } catch (error) {
            console.error('Error loading photos:', error);
        }
    }

    updatePhotosDisplay() {
        const photosGrid = document.getElementById('photosGrid');
        photosGrid.innerHTML = '';

        this.photos.forEach(photo => {
            const photoCard = document.createElement('div');
            photoCard.className = 'photo-card';
            photoCard.innerHTML = `
                <img src="${photo.url}" alt="Photo" class="photo-preview">
                <div class="photo-info">
                    <div class="photo-user">${photo.userName}</div>
                    <div class="photo-status">Статус: ${photo.status === 'verified' ? 'Проверено' : 'На модерации'}</div>
                    <div class="photo-actions">
                        <button class="btn btn-small btn-success" onclick="adminPanel.approvePhoto(${photo.id})">Одобрить</button>
                        <button class="btn btn-small btn-danger" onclick="adminPanel.rejectPhoto(${photo.id})">Отклонить</button>
                    </div>
                </div>
            `;
            photosGrid.appendChild(photoCard);
        });
    }

    loadSettings() {
        // Load current settings
        document.getElementById('nsfwThreshold').value = this.stats.nsfwThreshold || 0.7;
    }

    async searchUsers() {
        const searchTerm = document.getElementById('userSearch').value;
        if (!searchTerm) return;

        try {
            const response = await fetch(`/api/admin/users/search?q=${encodeURIComponent(searchTerm)}`, {
                headers: {
                    'Authorization': `Bearer ${this.getAuthToken()}`
                }
            });

            if (response.ok) {
                const data = await response.json();
                this.users = data.users;
                this.updateUsersDisplay();
            }
        } catch (error) {
            console.error('Error searching users:', error);
        }
    }

    filterPhotos(filter) {
        this.currentPage = 1;
        this.loadPhotos();
    }

    async viewUser(userId) {
        try {
            const response = await fetch(`/api/admin/users/${userId}`, {
                headers: {
                    'Authorization': `Bearer ${this.getAuthToken()}`
                }
            });

            if (response.ok) {
                const user = await response.json();
                this.showUserModal(user);
            }
        } catch (error) {
            console.error('Error loading user details:', error);
        }
    }

    showUserModal(user) {
        const modal = document.getElementById('userModal');
        const userDetails = document.getElementById('userDetails');
        
        userDetails.innerHTML = `
            <div class="user-details">
                <div class="user-header">
                    <img src="${user.avatar || '/images/default-avatar.png'}" alt="${user.name}" class="user-avatar-large">
                    <div class="user-info">
                        <h3>${user.name}</h3>
                        <p>@${user.username || 'no_username'}</p>
                        <p>ID: ${user.id}</p>
                        <p>Статус: ${user.status === 'active' ? 'Активен' : 'Забанен'}</p>
                    </div>
                </div>
                <div class="user-stats">
                    <div class="stat">
                        <span class="stat-label">Профиль создан:</span>
                        <span class="stat-value">${new Date(user.createdAt).toLocaleDateString()}</span>
                    </div>
                    <div class="stat">
                        <span class="stat-label">Последняя активность:</span>
                        <span class="stat-value">${new Date(user.lastActive).toLocaleDateString()}</span>
                    </div>
                    <div class="stat">
                        <span class="stat-label">Фото:</span>
                        <span class="stat-value">${user.photosCount || 0}</span>
                    </div>
                    <div class="stat">
                        <span class="stat-label">Матчи:</span>
                        <span class="stat-value">${user.matchesCount || 0}</span>
                    </div>
                </div>
                <div class="user-actions">
                    <button class="btn btn-primary" onclick="adminPanel.editUser(${user.id})">Редактировать</button>
                    <button class="btn ${user.status === 'active' ? 'btn-danger' : 'btn-success'}" onclick="adminPanel.toggleUserStatus(${user.id})">
                        ${user.status === 'active' ? 'Забанить' : 'Разбанить'}
                    </button>
                </div>
            </div>
        `;
        
        modal.classList.remove('hidden');
    }

    closeModal() {
        document.getElementById('userModal').classList.add('hidden');
    }

    async toggleUserStatus(userId) {
        try {
            const user = this.users.find(u => u.id === userId);
            const newStatus = user.status === 'active' ? 'banned' : 'active';
            
            const response = await fetch(`/api/admin/users/${userId}/status`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.getAuthToken()}`
                },
                body: JSON.stringify({ status: newStatus })
            });

            if (response.ok) {
                this.tg.showAlert(`Пользователь ${newStatus === 'banned' ? 'забанен' : 'разбанен'}`);
                this.loadUsers();
                this.closeModal();
            }
        } catch (error) {
            console.error('Error toggling user status:', error);
        }
    }

    async approvePhoto(photoId) {
        try {
            const response = await fetch(`/api/admin/photos/${photoId}/approve`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${this.getAuthToken()}`
                }
            });

            if (response.ok) {
                this.tg.showAlert('Фото одобрено');
                this.loadPhotos();
            }
        } catch (error) {
            console.error('Error approving photo:', error);
        }
    }

    async rejectPhoto(photoId) {
        try {
            const response = await fetch(`/api/admin/photos/${photoId}/reject`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${this.getAuthToken()}`
                }
            });

            if (response.ok) {
                this.tg.showAlert('Фото отклонено');
                this.loadPhotos();
            }
        } catch (error) {
            console.error('Error rejecting photo:', error);
        }
    }

    async createAdmin() {
        try {
            const formData = new FormData(document.getElementById('createAdminForm'));
            const adminData = Object.fromEntries(formData.entries());
            
            const response = await fetch('/api/admin/create', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.getAuthToken()}`
                },
                body: JSON.stringify(adminData)
            });

            if (response.ok) {
                this.tg.showAlert('Администратор создан успешно!');
                document.getElementById('createAdminForm').reset();
            } else {
                const error = await response.json();
                this.tg.showAlert(`Ошибка: ${error.message}`);
            }
        } catch (error) {
            console.error('Error creating admin:', error);
            this.tg.showAlert('Ошибка создания администратора');
        }
    }

    updatePagination(type, total, page, pages) {
        const pagination = document.getElementById(`${type}Pagination`);
        pagination.innerHTML = '';

        // Previous button
        const prevBtn = document.createElement('button');
        prevBtn.textContent = '←';
        prevBtn.disabled = page === 1;
        prevBtn.onclick = () => {
            this.currentPage = page - 1;
            this.loadSectionData(this.currentSection);
        };
        pagination.appendChild(prevBtn);

        // Page numbers
        for (let i = Math.max(1, page - 2); i <= Math.min(pages, page + 2); i++) {
            const pageBtn = document.createElement('button');
            pageBtn.textContent = i;
            pageBtn.className = i === page ? 'active' : '';
            pageBtn.onclick = () => {
                this.currentPage = i;
                this.loadSectionData(this.currentSection);
            };
            pagination.appendChild(pageBtn);
        }

        // Next button
        const nextBtn = document.createElement('button');
        nextBtn.textContent = '→';
        nextBtn.disabled = page === pages;
        nextBtn.onclick = () => {
            this.currentPage = page + 1;
            this.loadSectionData(this.currentSection);
        };
        pagination.appendChild(nextBtn);
    }

    handleBackButton() {
        if (this.currentScreen === 'dashboard') {
            this.tg.close();
        } else {
            this.showScreen('dashboard');
        }
    }

    updateNavigation() {
        switch (this.currentScreen) {
            case 'login':
                this.tg.BackButton.hide();
                this.tg.MainButton.hide();
                break;
            case 'dashboard':
                this.tg.BackButton.show();
                this.tg.MainButton.hide();
                break;
        }
    }

    getAuthToken() {
        return localStorage.getItem('adminToken');
    }

    showError(message) {
        const errorDiv = document.getElementById('loginError');
        errorDiv.textContent = message;
        errorDiv.classList.remove('hidden');
        setTimeout(() => {
            errorDiv.classList.add('hidden');
        }, 5000);
    }
}

// Initialize the admin panel when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.adminPanel = new AdminPanel();
});

// Export for global access
window.AdminPanel = AdminPanel;
