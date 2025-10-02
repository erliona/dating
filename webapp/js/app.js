/**
 * Modern Dating Mini App
 * Following Telegram Mini App Best Practices 2024
 */

// Initialize Telegram WebApp
const tg = window.Telegram?.WebApp;
if (tg) {
    tg.ready();
    tg.expand();
    tg.enableClosingConfirmation();
}

// App state
const state = {
    currentScreen: 'loading',
    user: null,
    profile: null,
    cards: [],
    currentCardIndex: 0,
    matches: [],
};

// API service layer (separation of concerns)
const api = {
    async getUserProfile() {
        // In real implementation, this would fetch from backend
        // For now, return mock data or null
        return null;
    },

    async saveProfile(profileData) {
        // Send profile data to bot via Telegram WebApp
        if (!tg) {
            throw new Error('Telegram WebApp not available');
        }

        const payload = {
            action: 'create_profile',
            ...profileData
        };

        tg.sendData(JSON.stringify(payload));
    },

    async deleteProfile() {
        if (!tg) {
            throw new Error('Telegram WebApp not available');
        }

        const payload = { action: 'delete' };
        tg.sendData(JSON.stringify(payload));
    },

    async sendInteraction(targetUserId, actionType) {
        // Queue interaction locally
        const interactions = JSON.parse(localStorage.getItem('interactions_queue') || '[]');
        interactions.push({
            target_user_id: targetUserId,
            action: actionType,
            timestamp: Date.now()
        });
        localStorage.setItem('interactions_queue', JSON.stringify(interactions));
    },

    async getRecommendations() {
        // Mock recommendations - in real app, fetch from backend
        return [
            {
                user_id: 101,
                name: 'Анна',
                age: 25,
                bio: 'Люблю путешествия и фотографию',
                location: 'Москва',
                interests: ['Путешествия', 'Фотография'],
                photo_url: null
            },
            {
                user_id: 102,
                name: 'Дмитрий',
                age: 28,
                bio: 'Программист и музыкант',
                location: 'Санкт-Петербург',
                interests: ['Музыка', 'IT'],
                photo_url: null
            }
        ];
    },

    async getMatches() {
        // Mock matches - in real app, fetch from backend
        return [];
    }
};

// UI Controller
const ui = {
    showScreen(screenId) {
        // Hide all screens
        document.querySelectorAll('.screen').forEach(screen => {
            screen.style.display = 'none';
        });

        // Show target screen
        const screen = document.getElementById(screenId);
        if (screen) {
            screen.style.display = 'block';
            state.currentScreen = screenId;
        }
    },

    showError(message) {
        const errorElement = document.getElementById('error-message');
        if (errorElement) {
            errorElement.textContent = message;
        }
        this.showScreen('error');
    },

    showLoading() {
        this.showScreen('loading');
    },

    showProfileForm(profile = null) {
        if (profile) {
            // Fill form with existing profile data
            Object.keys(profile).forEach(key => {
                const input = document.getElementById(key);
                if (input) {
                    if (key === 'interests' && Array.isArray(profile[key])) {
                        input.value = profile[key].join(', ');
                    } else {
                        input.value = profile[key] || '';
                    }
                }
            });

            // Show delete button
            const deleteBtn = document.getElementById('deleteProfile');
            if (deleteBtn) {
                deleteBtn.style.display = 'block';
            }
        }

        this.showScreen('profile-form');
    },

    showDiscover() {
        this.showScreen('discover');
        this.loadCards();
    },

    showMatches() {
        this.showScreen('matches');
        this.loadMatches();
    },

    async loadCards() {
        try {
            const cards = await api.getRecommendations();
            state.cards = cards;
            state.currentCardIndex = 0;
            this.renderCards();
        } catch (error) {
            console.error('Error loading cards:', error);
            this.showError('Не удалось загрузить рекомендации');
        }
    },

    renderCards() {
        const container = document.getElementById('cards-stack');
        const noMoreCards = document.getElementById('no-more-cards');

        if (!container) return;

        if (state.currentCardIndex >= state.cards.length) {
            container.innerHTML = '';
            if (noMoreCards) {
                noMoreCards.style.display = 'block';
            }
            return;
        }

        if (noMoreCards) {
            noMoreCards.style.display = 'none';
        }

        const card = state.cards[state.currentCardIndex];
        container.innerHTML = `
            <div class="profile-card" data-user-id="${card.user_id}">
                <div class="card-photo">
                    ${card.photo_url 
                        ? `<img src="${card.photo_url}" alt="${card.name}">` 
                        : '<div class="photo-placeholder">📷</div>'
                    }
                </div>
                <div class="card-content">
                    <h2>${card.name}, ${card.age}</h2>
                    ${card.location ? `<p class="location">📍 ${card.location}</p>` : ''}
                    ${card.bio ? `<p class="bio">${card.bio}</p>` : ''}
                    ${card.interests && card.interests.length > 0 
                        ? `<div class="interests">${card.interests.map(i => `<span class="interest-tag">${i}</span>`).join('')}</div>` 
                        : ''
                    }
                </div>
            </div>
        `;
    },

    async handleLike() {
        if (state.currentCardIndex >= state.cards.length) return;

        const card = state.cards[state.currentCardIndex];
        
        try {
            await api.sendInteraction(card.user_id, 'like');
            
            // Haptic feedback
            if (tg?.HapticFeedback) {
                tg.HapticFeedback.impactOccurred('medium');
            }

            this.nextCard();
        } catch (error) {
            console.error('Error sending like:', error);
        }
    },

    async handleDislike() {
        if (state.currentCardIndex >= state.cards.length) return;

        const card = state.cards[state.currentCardIndex];
        
        try {
            await api.sendInteraction(card.user_id, 'dislike');
            
            // Haptic feedback
            if (tg?.HapticFeedback) {
                tg.HapticFeedback.impactOccurred('light');
            }

            this.nextCard();
        } catch (error) {
            console.error('Error sending dislike:', error);
        }
    },

    nextCard() {
        state.currentCardIndex++;
        this.renderCards();
    },

    async loadMatches() {
        try {
            const matches = await api.getMatches();
            state.matches = matches;
            this.renderMatches();
        } catch (error) {
            console.error('Error loading matches:', error);
        }
    },

    renderMatches() {
        const container = document.getElementById('matches-list');
        if (!container) return;

        if (state.matches.length === 0) {
            container.innerHTML = '<p class="empty-state">У тебя пока нет матчей. Продолжай смотреть анкеты!</p>';
            return;
        }

        container.innerHTML = state.matches.map(match => `
            <div class="match-card">
                <div class="match-photo">
                    ${match.photo_url 
                        ? `<img src="${match.photo_url}" alt="${match.name}">` 
                        : '<div class="photo-placeholder">📷</div>'
                    }
                </div>
                <div class="match-info">
                    <h3>${match.name}, ${match.age}</h3>
                    ${match.location ? `<p>📍 ${match.location}</p>` : ''}
                </div>
            </div>
        `).join('');
    }
};

// Form validation
function validateForm(formData) {
    const errors = [];

    if (!formData.name || formData.name.length < 2) {
        errors.push('Имя должно быть не менее 2 символов');
    }

    const age = parseInt(formData.age);
    if (!age || age < 18 || age > 120) {
        errors.push('Возраст должен быть от 18 до 120 лет');
    }

    if (!formData.gender) {
        errors.push('Выберите пол');
    }

    if (!formData.preference) {
        errors.push('Выберите, кого ищете');
    }

    if (formData.bio && formData.bio.length > 400) {
        errors.push('Описание не должно превышать 400 символов');
    }

    if (formData.photo_url && formData.photo_url.length > 0) {
        try {
            const url = new URL(formData.photo_url);
            if (url.protocol !== 'https:') {
                errors.push('Ссылка на фото должна использовать HTTPS');
            }
        } catch {
            errors.push('Некорректная ссылка на фото');
        }
    }

    return errors;
}

// Event handlers
function setupEventListeners() {
    // Profile form submission
    const profileForm = document.getElementById('profileForm');
    if (profileForm) {
        profileForm.addEventListener('submit', async (e) => {
            e.preventDefault();

            const formData = new FormData(profileForm);
            const data = {};
            
            formData.forEach((value, key) => {
                if (value && value.trim()) {
                    if (key === 'interests') {
                        data[key] = value.split(',').map(i => i.trim()).filter(i => i);
                    } else {
                        data[key] = value.trim();
                    }
                }
            });

            // Validate
            const errors = validateForm(data);
            if (errors.length > 0) {
                alert(errors.join('\n'));
                return;
            }

            // Add queued interactions
            const queuedInteractions = localStorage.getItem('interactions_queue');
            if (queuedInteractions) {
                data.queued_interactions = JSON.parse(queuedInteractions);
                localStorage.removeItem('interactions_queue');
            }

            try {
                await api.saveProfile(data);
                // WebApp will close after sendData
            } catch (error) {
                ui.showError('Не удалось сохранить профиль: ' + error.message);
            }
        });
    }

    // Delete profile
    const deleteBtn = document.getElementById('deleteProfile');
    if (deleteBtn) {
        deleteBtn.addEventListener('click', async () => {
            if (confirm('Вы уверены, что хотите удалить профиль?')) {
                try {
                    await api.deleteProfile();
                    // WebApp will close after sendData
                } catch (error) {
                    ui.showError('Не удалось удалить профиль: ' + error.message);
                }
            }
        });
    }

    // Like/Dislike buttons
    const likeBtn = document.getElementById('likeBtn');
    const dislikeBtn = document.getElementById('dislikeBtn');

    if (likeBtn) {
        likeBtn.addEventListener('click', () => ui.handleLike());
    }

    if (dislikeBtn) {
        dislikeBtn.addEventListener('click', () => ui.handleDislike());
    }

    // Navigation buttons
    const navButtons = [
        { id: 'navProfile', action: () => ui.showProfileForm(state.profile) },
        { id: 'navProfile2', action: () => ui.showProfileForm(state.profile) },
        { id: 'navDiscover', action: () => ui.showDiscover() },
        { id: 'navDiscover2', action: () => ui.showDiscover() },
        { id: 'navMatches', action: () => ui.showMatches() },
        { id: 'navMatches2', action: () => ui.showMatches() },
    ];

    navButtons.forEach(({ id, action }) => {
        const btn = document.getElementById(id);
        if (btn) {
            btn.addEventListener('click', action);
        }
    });

    // Retry button
    const retryBtn = document.getElementById('retryBtn');
    if (retryBtn) {
        retryBtn.addEventListener('click', () => init());
    }

    // Swipe gestures (touch support)
    const cardsContainer = document.getElementById('cards-stack');
    if (cardsContainer) {
        let startX = 0;
        let startY = 0;

        cardsContainer.addEventListener('touchstart', (e) => {
            startX = e.touches[0].clientX;
            startY = e.touches[0].clientY;
        });

        cardsContainer.addEventListener('touchend', (e) => {
            const endX = e.changedTouches[0].clientX;
            const endY = e.changedTouches[0].clientY;
            const deltaX = endX - startX;
            const deltaY = endY - startY;

            // Horizontal swipe
            if (Math.abs(deltaX) > Math.abs(deltaY) && Math.abs(deltaX) > 50) {
                if (deltaX > 0) {
                    // Swipe right = like
                    ui.handleLike();
                } else {
                    // Swipe left = dislike
                    ui.handleDislike();
                }
            }
        });
    }
}

// App initialization
async function init() {
    try {
        ui.showLoading();

        // Try to load user profile
        const profile = await api.getUserProfile();
        state.profile = profile;

        if (profile) {
            // User has profile, show discover screen
            ui.showDiscover();
        } else {
            // No profile, show profile form
            ui.showProfileForm();
        }

        setupEventListeners();
    } catch (error) {
        console.error('Initialization error:', error);
        ui.showError('Не удалось загрузить приложение');
    }
}

// Start app
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}

// Handle Telegram theme changes
if (tg) {
    tg.onEvent('themeChanged', () => {
        // Update app theme based on Telegram theme
        const theme = tg.colorScheme;
        document.body.className = theme === 'dark' ? 'theme-dark' : 'theme-light';
    });

    // Set initial theme
    document.body.className = tg.colorScheme === 'dark' ? 'theme-dark' : 'theme-light';
}
