// Telegram WebApp Integration
class DatingApp {
    constructor() {
        this.tg = window.Telegram.WebApp;
        this.currentScreen = 'loading';
        this.user = null;
        this.profile = null;
        this.matches = [];
        this.currentProfile = null;
        
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
        
        // Start the app
        this.startApp();
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
        // Welcome screen
        document.getElementById('startDatingBtn').addEventListener('click', () => {
            this.startDating();
        });

        // Onboarding form
        document.getElementById('onboardingForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.submitOnboarding();
        });

        // Photo upload
        this.setupPhotoUpload();

        // Profile screen
        document.getElementById('editProfileBtn').addEventListener('click', () => {
            this.editProfile();
        });

        // Discovery screen
        document.getElementById('likeBtn').addEventListener('click', () => {
            this.likeProfile();
        });

        document.getElementById('dislikeBtn').addEventListener('click', () => {
            this.dislikeProfile();
        });

        document.getElementById('superlikeBtn').addEventListener('click', () => {
            this.superlikeProfile();
        });

        // Settings
        this.setupSettings();
    }

    setupPhotoUpload() {
        const photoInputs = document.querySelectorAll('.photo-input');
        photoInputs.forEach((input, index) => {
            input.addEventListener('change', (e) => {
                this.handlePhotoUpload(e, index + 1);
            });
        });
    }

    setupSettings() {
        // Privacy settings
        document.getElementById('hideAge').addEventListener('change', (e) => {
            this.updatePrivacySetting('hideAge', e.target.checked);
        });

        document.getElementById('hideDistance').addEventListener('change', (e) => {
            this.updatePrivacySetting('hideDistance', e.target.checked);
        });

        document.getElementById('hideOnline').addEventListener('change', (e) => {
            this.updatePrivacySetting('hideOnline', e.target.checked);
        });

        // Notification settings
        document.getElementById('notifyMatches').addEventListener('change', (e) => {
            this.updateNotificationSetting('notifyMatches', e.target.checked);
        });

        document.getElementById('notifyLikes').addEventListener('change', (e) => {
            this.updateNotificationSetting('notifyLikes', e.target.checked);
        });

        document.getElementById('notifyMessages').addEventListener('change', (e) => {
            this.updateNotificationSetting('notifyMessages', e.target.checked);
        });

        // Delete account
        document.getElementById('deleteAccountBtn').addEventListener('click', () => {
            this.deleteAccount();
        });
    }

    async startApp() {
        try {
            // Show loading screen
            this.showScreen('loading');
            
            // Get user data from Telegram
            this.user = this.tg.initDataUnsafe?.user;
            
            if (!this.user) {
                throw new Error('User data not available');
            }

            // Check if user has profile
            const hasProfile = await this.checkUserProfile();
            
            if (hasProfile) {
                await this.loadUserProfile();
                this.showScreen('profile');
            } else {
                this.showScreen('welcome');
            }
            
        } catch (error) {
            console.error('Error starting app:', error);
            this.showError('Ошибка инициализации приложения');
        }
    }

    async checkUserProfile() {
        try {
            const response = await fetch('/api/profiles/me', {
                headers: {
                    'Authorization': `Bearer ${this.getAuthToken()}`
                }
            });
            return response.ok;
        } catch (error) {
            return false;
        }
    }

    async loadUserProfile() {
        try {
            const response = await fetch('/api/profiles/me', {
                headers: {
                    'Authorization': `Bearer ${this.getAuthToken()}`
                }
            });
            
            if (response.ok) {
                this.profile = await response.json();
                this.updateProfileDisplay();
            }
        } catch (error) {
            console.error('Error loading profile:', error);
        }
    }

    startDating() {
        this.showScreen('onboarding');
        this.tg.MainButton.setText('Создать профиль');
        this.tg.MainButton.show();
        this.tg.MainButton.onClick(() => {
            document.getElementById('onboardingForm').dispatchEvent(new Event('submit'));
        });
    }

    async submitOnboarding() {
        try {
            this.tg.MainButton.showProgress();
            
            const formData = new FormData(document.getElementById('onboardingForm'));
            const profileData = Object.fromEntries(formData.entries());
            
            // Add Telegram user data
            profileData.telegram_id = this.user.id;
            profileData.username = this.user.username;
            profileData.first_name = this.user.first_name;
            profileData.last_name = this.user.last_name;
            
            const response = await fetch('/api/profiles', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.getAuthToken()}`
                },
                body: JSON.stringify(profileData)
            });

            if (response.ok) {
                this.profile = await response.json();
                this.tg.showAlert('Профиль создан успешно!');
                this.tg.MainButton.hide();
                this.showScreen('profile');
            } else {
                const error = await response.json();
                this.tg.showAlert(`Ошибка: ${error.message}`);
            }
        } catch (error) {
            console.error('Error creating profile:', error);
            this.tg.showAlert('Ошибка создания профиля');
        } finally {
            this.tg.MainButton.hideProgress();
        }
    }

    handlePhotoUpload(event, photoNumber) {
        const file = event.target.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = (e) => {
                const preview = document.getElementById(`photoPreview${photoNumber}`);
                const img = document.createElement('img');
                img.src = e.target.result;
                img.style.width = '100%';
                img.style.height = '100%';
                img.style.objectFit = 'cover';
                preview.innerHTML = '';
                preview.appendChild(img);
            };
            reader.readAsDataURL(file);
        }
    }

    editProfile() {
        // Navigate to profile editing
        this.tg.showAlert('Функция редактирования профиля будет добавлена в следующей версии');
    }

    async likeProfile() {
        if (!this.currentProfile) return;
        
        try {
            const response = await fetch(`/api/discovery/like/${this.currentProfile.id}`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${this.getAuthToken()}`
                }
            });

            if (response.ok) {
                this.tg.HapticFeedback.impactOccurred('medium');
                this.tg.showAlert('Лайк отправлен!');
                this.loadNextProfile();
            }
        } catch (error) {
            console.error('Error liking profile:', error);
        }
    }

    async dislikeProfile() {
        if (!this.currentProfile) return;
        
        try {
            const response = await fetch(`/api/discovery/dislike/${this.currentProfile.id}`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${this.getAuthToken()}`
                }
            });

            if (response.ok) {
                this.tg.HapticFeedback.impactOccurred('light');
                this.loadNextProfile();
            }
        } catch (error) {
            console.error('Error disliking profile:', error);
        }
    }

    async superlikeProfile() {
        if (!this.currentProfile) return;
        
        try {
            const response = await fetch(`/api/discovery/superlike/${this.currentProfile.id}`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${this.getAuthToken()}`
                }
            });

            if (response.ok) {
                this.tg.HapticFeedback.impactOccurred('heavy');
                this.tg.showAlert('Суперлайк отправлен!');
                this.loadNextProfile();
            }
        } catch (error) {
            console.error('Error superliking profile:', error);
        }
    }

    async loadNextProfile() {
        try {
            const response = await fetch('/api/discovery/next', {
                headers: {
                    'Authorization': `Bearer ${this.getAuthToken()}`
                }
            });

            if (response.ok) {
                this.currentProfile = await response.json();
                this.updateDiscoveryDisplay();
            } else {
                this.tg.showAlert('Больше профилей не найдено');
            }
        } catch (error) {
            console.error('Error loading next profile:', error);
        }
    }

    updateProfileDisplay() {
        if (!this.profile) return;
        
        document.getElementById('profileName').textContent = this.profile.name;
        document.getElementById('profileAge').textContent = `${this.profile.age} лет`;
        document.getElementById('profileLocation').textContent = this.profile.city;
        document.getElementById('profileBio').textContent = this.profile.bio || 'Биография не указана';
        
        if (this.profile.photos && this.profile.photos.length > 0) {
            document.getElementById('mainPhoto').src = this.profile.photos[0];
        }
    }

    updateDiscoveryDisplay() {
        if (!this.currentProfile) return;
        
        document.getElementById('discoveryName').textContent = this.currentProfile.name;
        document.getElementById('discoveryAge').textContent = `${this.currentProfile.age} лет`;
        document.getElementById('discoveryLocation').textContent = this.currentProfile.city;
        document.getElementById('discoveryBio').textContent = this.currentProfile.bio || 'Биография не указана';
        
        if (this.currentProfile.photos && this.currentProfile.photos.length > 0) {
            document.getElementById('discoveryPhoto').src = this.currentProfile.photos[0];
        }
    }

    updatePrivacySetting(setting, value) {
        // Update privacy setting
        console.log(`Privacy setting ${setting}: ${value}`);
    }

    updateNotificationSetting(setting, value) {
        // Update notification setting
        console.log(`Notification setting ${setting}: ${value}`);
    }

    deleteAccount() {
        this.tg.showConfirm('Вы уверены, что хотите удалить аккаунт? Это действие нельзя отменить.', (confirmed) => {
            if (confirmed) {
                this.tg.showAlert('Функция удаления аккаунта будет добавлена в следующей версии');
            }
        });
    }

    handleBackButton() {
        switch (this.currentScreen) {
            case 'onboarding':
                this.showScreen('welcome');
                break;
            case 'profile':
                this.tg.close();
                break;
            case 'discovery':
                this.showScreen('profile');
                break;
            case 'matches':
                this.showScreen('profile');
                break;
            case 'settings':
                this.showScreen('profile');
                break;
            default:
                this.tg.close();
        }
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

    updateNavigation() {
        switch (this.currentScreen) {
            case 'welcome':
                this.tg.BackButton.hide();
                this.tg.MainButton.hide();
                break;
            case 'onboarding':
                this.tg.BackButton.show();
                this.tg.MainButton.setText('Создать профиль');
                this.tg.MainButton.show();
                break;
            case 'profile':
                this.tg.BackButton.hide();
                this.tg.MainButton.hide();
                break;
            case 'discovery':
                this.tg.BackButton.show();
                this.tg.MainButton.hide();
                break;
            case 'matches':
                this.tg.BackButton.show();
                this.tg.MainButton.hide();
                break;
            case 'settings':
                this.tg.BackButton.show();
                this.tg.MainButton.hide();
                break;
        }
    }

    getAuthToken() {
        // Get auth token from Telegram init data
        return this.tg.initData;
    }

    showError(message) {
        this.tg.showAlert(message);
    }

    // Navigation methods
    goToDiscovery() {
        this.showScreen('discovery');
        this.loadNextProfile();
    }

    goToMatches() {
        this.showScreen('matches');
        this.loadMatches();
    }

    goToSettings() {
        this.showScreen('settings');
    }

    async loadMatches() {
        try {
            const response = await fetch('/api/matches', {
                headers: {
                    'Authorization': `Bearer ${this.getAuthToken()}`
                }
            });

            if (response.ok) {
                this.matches = await response.json();
                this.updateMatchesDisplay();
            }
        } catch (error) {
            console.error('Error loading matches:', error);
        }
    }

    updateMatchesDisplay() {
        const matchesList = document.getElementById('matchesList');
        matchesList.innerHTML = '';

        this.matches.forEach(match => {
            const matchElement = document.createElement('div');
            matchElement.className = 'match-item';
            matchElement.innerHTML = `
                <div class="match-photo">
                    <img src="${match.photos[0] || '/images/default-avatar.png'}" alt="${match.name}">
                </div>
                <div class="match-name">${match.name}</div>
                <div class="match-age">${match.age} лет</div>
            `;
            matchElement.addEventListener('click', () => {
                this.openChat(match.id);
            });
            matchesList.appendChild(matchElement);
        });
    }

    openChat(matchId) {
        this.tg.showAlert('Функция чата будет добавлена в следующей версии');
    }
}

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.datingApp = new DatingApp();
});

// Export for global access
window.DatingApp = DatingApp;
