/**
 * Discovery/Swipes functionality for Dating Mini App
 * Epic C: Discovery, Swipes, Matches, Favorites
 */

// ============================================================================
// State Management
// ============================================================================

let currentCards = [];
let currentCardIndex = 0;
let discoveryCursor = null;
let filters = {
    age_min: null,
    age_max: null,
    height_min: null,
    height_max: null,
    goal: null,
    education: null,
    verified_only: false
};
let matches = [];
let favorites = [];

// Touch/Swipe handling
let touchStartX = 0;
let touchStartY = 0;
let isDragging = false;
let currentCard = null;

// ============================================================================
// Discovery Functions
// ============================================================================

/**
 * Show discovery screen and load cards
 */
async function showDiscovery() {
    hideAllScreens();
    document.getElementById('discovery-screen').classList.remove('hidden');
    triggerHaptic('impact', 'light');
    
    // Load cards if empty
    if (currentCards.length === 0) {
        await loadDiscoveryCards();
    }
    
    // Update matches badge
    updateMatchesBadge();
}

/**
 * Load discovery cards from API
 */
async function loadDiscoveryCards() {
    try {
        // Build query parameters
        const params = new URLSearchParams({
            limit: '10'
        });
        
        if (discoveryCursor) params.append('cursor', discoveryCursor);
        if (filters.age_min) params.append('age_min', filters.age_min);
        if (filters.age_max) params.append('age_max', filters.age_max);
        if (filters.height_min) params.append('height_min', filters.height_min);
        if (filters.height_max) params.append('height_max', filters.height_max);
        if (filters.goal) params.append('goal', filters.goal);
        if (filters.education) params.append('education', filters.education);
        if (filters.verified_only) params.append('verified_only', 'true');
        
        const response = await fetch(`${API_BASE_URL}/api/discover?${params}`, {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });
        
        if (!response.ok) {
            throw new Error('Failed to load cards');
        }
        
        const data = await response.json();
        
        currentCards = data.profiles || [];
        discoveryCursor = data.next_cursor;
        currentCardIndex = 0;
        
        renderCurrentCard();
    } catch (error) {
        console.error('Error loading discovery cards:', error);
        showEmptyState();
    }
}

/**
 * Render current card in the stack
 */
function renderCurrentCard() {
    const cardStack = document.getElementById('cardStack');
    const emptyState = document.getElementById('emptyState');
    const actionButtons = document.getElementById('actionButtons');
    
    if (currentCardIndex >= currentCards.length) {
        // No more cards, load more or show empty state
        if (discoveryCursor) {
            loadDiscoveryCards();
        } else {
            showEmptyState();
        }
        return;
    }
    
    emptyState.style.display = 'none';
    actionButtons.style.display = 'flex';
    
    const profile = currentCards[currentCardIndex];
    const card = createProfileCard(profile);
    
    cardStack.innerHTML = '';
    cardStack.appendChild(card);
    
    // Initialize swipe handlers
    initializeSwipeHandlers(card);
}

/**
 * Create profile card element
 */
function createProfileCard(profile) {
    const card = document.createElement('div');
    card.className = 'profile-card';
    card.dataset.userId = profile.user_id;
    
    const photo = profile.photos && profile.photos.length > 0 
        ? profile.photos[0].url 
        : 'https://via.placeholder.com/400x600?text=No+Photo';
    
    const verifiedBadge = profile.photos && profile.photos[0]?.is_verified 
        ? '<span class="verified-badge">✓</span>' 
        : '';
    
    const interests = profile.interests && profile.interests.length > 0
        ? profile.interests.slice(0, 5).map(i => `<span class="interest-tag">${i}</span>`).join('')
        : '';
    
    card.innerHTML = `
        <div class="card-image" style="background-image: url('${photo}')">
            ${verifiedBadge}
        </div>
        <div class="card-info">
            <div class="card-header">
                <h3>${profile.name}, ${profile.age}</h3>
                ${profile.city ? `<p class="card-location">📍 ${profile.city}</p>` : ''}
            </div>
            ${profile.bio ? `<p class="card-bio">${profile.bio}</p>` : ''}
            ${interests ? `<div class="card-interests">${interests}</div>` : ''}
            <div class="card-details">
                ${profile.height_cm ? `<span>📏 ${profile.height_cm} см</span>` : ''}
                ${profile.education ? `<span>🎓 ${formatEducation(profile.education)}</span>` : ''}
                ${profile.goal ? `<span>💫 ${formatGoal(profile.goal)}</span>` : ''}
            </div>
        </div>
        <div class="swipe-indicator swipe-left hidden">
            <svg width="60" height="60" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
                <line x1="18" y1="6" x2="6" y2="18"></line>
                <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
        </div>
        <div class="swipe-indicator swipe-right hidden">
            <svg width="60" height="60" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
                <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"></path>
            </svg>
        </div>
    `;
    
    return card;
}

/**
 * Show empty state
 */
function showEmptyState() {
    const emptyState = document.getElementById('emptyState');
    const actionButtons = document.getElementById('actionButtons');
    
    emptyState.style.display = 'flex';
    actionButtons.style.display = 'none';
}

// ============================================================================
// Swipe Handlers
// ============================================================================

/**
 * Initialize swipe handlers for a card
 */
function initializeSwipeHandlers(card) {
    currentCard = card;
    
    // Touch events
    card.addEventListener('touchstart', handleTouchStart, { passive: true });
    card.addEventListener('touchmove', handleTouchMove, { passive: false });
    card.addEventListener('touchend', handleTouchEnd);
    
    // Mouse events for desktop
    card.addEventListener('mousedown', handleMouseDown);
    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);
}

function handleTouchStart(e) {
    touchStartX = e.touches[0].clientX;
    touchStartY = e.touches[0].clientY;
    isDragging = true;
}

function handleTouchMove(e) {
    if (!isDragging) return;
    
    e.preventDefault();
    
    const touchX = e.touches[0].clientX;
    const touchY = e.touches[0].clientY;
    const deltaX = touchX - touchStartX;
    const deltaY = touchY - touchStartY;
    
    updateCardPosition(deltaX, deltaY);
}

function handleTouchEnd(e) {
    if (!isDragging) return;
    
    isDragging = false;
    
    const deltaX = currentCard.offsetLeft;
    
    if (Math.abs(deltaX) > 100) {
        // Swipe detected
        if (deltaX > 0) {
            animateSwipeRight();
            handleLike();
        } else {
            animateSwipeLeft();
            handlePass();
        }
    } else {
        // Return to center
        resetCardPosition();
    }
}

function handleMouseDown(e) {
    touchStartX = e.clientX;
    touchStartY = e.clientY;
    isDragging = true;
}

function handleMouseMove(e) {
    if (!isDragging) return;
    
    const deltaX = e.clientX - touchStartX;
    const deltaY = e.clientY - touchStartY;
    
    updateCardPosition(deltaX, deltaY);
}

function handleMouseUp(e) {
    if (!isDragging) return;
    
    isDragging = false;
    
    const deltaX = currentCard.offsetLeft;
    
    if (Math.abs(deltaX) > 100) {
        if (deltaX > 0) {
            animateSwipeRight();
            handleLike();
        } else {
            animateSwipeLeft();
            handlePass();
        }
    } else {
        resetCardPosition();
    }
}

/**
 * Update card position during drag
 */
function updateCardPosition(deltaX, deltaY) {
    if (!currentCard) return;
    
    const rotation = deltaX / 20;
    
    currentCard.style.transform = `translate(${deltaX}px, ${deltaY}px) rotate(${rotation}deg)`;
    currentCard.style.transition = 'none';
    
    // Show swipe indicators
    const leftIndicator = currentCard.querySelector('.swipe-left');
    const rightIndicator = currentCard.querySelector('.swipe-right');
    
    if (deltaX < -50) {
        leftIndicator.classList.remove('hidden');
        rightIndicator.classList.add('hidden');
    } else if (deltaX > 50) {
        rightIndicator.classList.remove('hidden');
        leftIndicator.classList.add('hidden');
    } else {
        leftIndicator.classList.add('hidden');
        rightIndicator.classList.add('hidden');
    }
}

/**
 * Reset card position
 */
function resetCardPosition() {
    if (!currentCard) return;
    
    currentCard.style.transform = 'translate(0, 0) rotate(0deg)';
    currentCard.style.transition = 'transform 0.3s ease';
    
    const leftIndicator = currentCard.querySelector('.swipe-left');
    const rightIndicator = currentCard.querySelector('.swipe-right');
    leftIndicator.classList.add('hidden');
    rightIndicator.classList.add('hidden');
}

/**
 * Animate swipe left
 */
function animateSwipeLeft() {
    if (!currentCard) return;
    
    currentCard.style.transform = 'translate(-150%, 0) rotate(-30deg)';
    currentCard.style.transition = 'transform 0.3s ease';
    
    setTimeout(() => {
        currentCardIndex++;
        renderCurrentCard();
    }, 300);
}

/**
 * Animate swipe right
 */
function animateSwipeRight() {
    if (!currentCard) return;
    
    currentCard.style.transform = 'translate(150%, 0) rotate(30deg)';
    currentCard.style.transition = 'transform 0.3s ease';
    
    setTimeout(() => {
        currentCardIndex++;
        renderCurrentCard();
    }, 300);
}

// ============================================================================
// Action Handlers
// ============================================================================

/**
 * Handle pass action
 */
async function handlePass() {
    triggerHaptic('impact', 'light');
    
    if (currentCardIndex >= currentCards.length) return;
    
    const profile = currentCards[currentCardIndex];
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/pass`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify({
                target_id: profile.user_id
            })
        });
        
        if (!response.ok) {
            throw new Error('Failed to pass');
        }
    } catch (error) {
        console.error('Error passing:', error);
    }
    
    // Card animation handled by swipe or button click
    if (!isDragging) {
        animateSwipeLeft();
    }
}

/**
 * Handle like action
 */
async function handleLike() {
    triggerHaptic('impact', 'medium');
    
    if (currentCardIndex >= currentCards.length) return;
    
    const profile = currentCards[currentCardIndex];
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/like`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify({
                target_id: profile.user_id,
                type: 'like'
            })
        });
        
        if (!response.ok) {
            throw new Error('Failed to like');
        }
        
        const data = await response.json();
        
        // Check if it's a match
        if (data.match_id) {
            triggerHaptic('notification', 'success');
            showMatchModal(profile);
            await loadMatches(); // Refresh matches
        }
    } catch (error) {
        console.error('Error liking:', error);
    }
    
    if (!isDragging) {
        animateSwipeRight();
    }
}

/**
 * Handle superlike action
 */
async function handleSuperlike() {
    triggerHaptic('impact', 'heavy');
    
    if (currentCardIndex >= currentCards.length) return;
    
    const profile = currentCards[currentCardIndex];
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/like`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify({
                target_id: profile.user_id,
                type: 'superlike'
            })
        });
        
        if (!response.ok) {
            throw new Error('Failed to superlike');
        }
        
        const data = await response.json();
        
        if (data.match_id) {
            triggerHaptic('notification', 'success');
            showMatchModal(profile);
            await loadMatches();
        }
    } catch (error) {
        console.error('Error superliking:', error);
    }
    
    // Animate up
    if (currentCard) {
        currentCard.style.transform = 'translate(0, -150%) rotate(0deg)';
        currentCard.style.transition = 'transform 0.3s ease';
        
        setTimeout(() => {
            currentCardIndex++;
            renderCurrentCard();
        }, 300);
    }
}

/**
 * Handle add to favorites
 */
async function handleAddFavorite() {
    triggerHaptic('impact', 'medium');
    
    if (currentCardIndex >= currentCards.length) return;
    
    const profile = currentCards[currentCardIndex];
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/favorites`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify({
                target_id: profile.user_id
            })
        });
        
        if (!response.ok) {
            throw new Error('Failed to add favorite');
        }
        
        triggerHaptic('notification', 'success');
        
        // Show temporary feedback
        if (tg && tg.showAlert) {
            tg.showAlert('Добавлено в избранное ⭐');
        }
    } catch (error) {
        console.error('Error adding favorite:', error);
    }
}

// ============================================================================
// Filters
// ============================================================================

/**
 * Show filters screen
 */
function showFilters() {
    hideAllScreens();
    document.getElementById('filters-screen').classList.remove('hidden');
    triggerHaptic('impact', 'light');
    
    // Populate current filter values
    document.getElementById('filterAgeMin').value = filters.age_min || '';
    document.getElementById('filterAgeMax').value = filters.age_max || '';
    document.getElementById('filterHeightMin').value = filters.height_min || '';
    document.getElementById('filterHeightMax').value = filters.height_max || '';
    document.getElementById('filterGoal').value = filters.goal || '';
    document.getElementById('filterEducation').value = filters.education || '';
    document.getElementById('filterVerifiedOnly').checked = filters.verified_only;
}

/**
 * Hide filters screen
 */
function hideFilters() {
    showDiscovery();
}

/**
 * Reset filters
 */
function resetFilters() {
    triggerHaptic('impact', 'light');
    
    filters = {
        age_min: null,
        age_max: null,
        height_min: null,
        height_max: null,
        goal: null,
        education: null,
        verified_only: false
    };
    
    showFilters();
}

/**
 * Apply filters
 */
async function applyFilters() {
    triggerHaptic('impact', 'medium');
    
    filters.age_min = document.getElementById('filterAgeMin').value || null;
    filters.age_max = document.getElementById('filterAgeMax').value || null;
    filters.height_min = document.getElementById('filterHeightMin').value || null;
    filters.height_max = document.getElementById('filterHeightMax').value || null;
    filters.goal = document.getElementById('filterGoal').value || null;
    filters.education = document.getElementById('filterEducation').value || null;
    filters.verified_only = document.getElementById('filterVerifiedOnly').checked;
    
    // Reset discovery
    currentCards = [];
    currentCardIndex = 0;
    discoveryCursor = null;
    
    // Load new cards with filters
    await showDiscovery();
}

// ============================================================================
// Matches
// ============================================================================

/**
 * Show matches screen
 */
async function showMatches() {
    hideAllScreens();
    document.getElementById('matches-screen').classList.remove('hidden');
    triggerHaptic('impact', 'light');
    
    await loadMatches();
}

/**
 * Load matches from API
 */
async function loadMatches() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/matches?limit=20`, {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });
        
        if (!response.ok) {
            throw new Error('Failed to load matches');
        }
        
        const data = await response.json();
        matches = data.matches || [];
        
        renderMatches();
        updateMatchesBadge();
    } catch (error) {
        console.error('Error loading matches:', error);
    }
}

/**
 * Render matches list
 */
function renderMatches() {
    const matchesList = document.getElementById('matchesList');
    
    if (matches.length === 0) {
        matchesList.innerHTML = `
            <div class="empty-state">
                <svg width="60" height="60" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                    <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"></path>
                </svg>
                <h3>Пока нет матчей</h3>
                <p>Начните ставить лайки анкетам</p>
            </div>
        `;
        return;
    }
    
    matchesList.innerHTML = matches.map(match => {
        const profile = match.profile;
        const photo = profile.photos && profile.photos.length > 0 
            ? profile.photos[0].url 
            : 'https://via.placeholder.com/80x80?text=No+Photo';
        
        return `
            <div class="match-item">
                <img src="${photo}" alt="${profile.name}" class="match-photo">
                <div class="match-info">
                    <h4>${profile.name}, ${profile.age}</h4>
                    <p>${profile.bio ? profile.bio.substring(0, 60) + '...' : 'Нет описания'}</p>
                </div>
                <button class="icon-button" onclick="openChat(${match.match_id})" title="Написать">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
                    </svg>
                </button>
            </div>
        `;
    }).join('');
}

/**
 * Update matches badge
 */
function updateMatchesBadge() {
    const badge = document.getElementById('matchesBadge');
    if (matches.length > 0) {
        badge.textContent = matches.length;
        badge.style.display = 'block';
    } else {
        badge.style.display = 'none';
    }
}

/**
 * Open chat (placeholder)
 */
function openChat(matchId) {
    triggerHaptic('impact', 'medium');
    
    if (tg && tg.showAlert) {
        tg.showAlert('Чат будет доступен в следующем обновлении');
    }
}

// ============================================================================
// Favorites
// ============================================================================

/**
 * Show favorites screen
 */
async function showFavorites() {
    hideAllScreens();
    document.getElementById('favorites-screen').classList.remove('hidden');
    triggerHaptic('impact', 'light');
    
    await loadFavorites();
}

/**
 * Load favorites from API
 */
async function loadFavorites() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/favorites?limit=20`, {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });
        
        if (!response.ok) {
            throw new Error('Failed to load favorites');
        }
        
        const data = await response.json();
        favorites = data.favorites || [];
        
        renderFavorites();
    } catch (error) {
        console.error('Error loading favorites:', error);
    }
}

/**
 * Render favorites list
 */
function renderFavorites() {
    const favoritesList = document.getElementById('favoritesList');
    
    if (favorites.length === 0) {
        favoritesList.innerHTML = `
            <div class="empty-state">
                <svg width="60" height="60" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                    <path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"></path>
                </svg>
                <h3>Нет избранных</h3>
                <p>Добавляйте интересные анкеты в избранное</p>
            </div>
        `;
        return;
    }
    
    favoritesList.innerHTML = favorites.map(favorite => {
        const profile = favorite.profile;
        const photo = profile.photos && profile.photos.length > 0 
            ? profile.photos[0].url 
            : 'https://via.placeholder.com/80x80?text=No+Photo';
        
        return `
            <div class="favorite-item">
                <img src="${photo}" alt="${profile.name}" class="favorite-photo">
                <div class="favorite-info">
                    <h4>${profile.name}, ${profile.age}</h4>
                    <p>${profile.bio ? profile.bio.substring(0, 60) + '...' : 'Нет описания'}</p>
                </div>
                <button class="icon-button" onclick="removeFavorite(${profile.user_id})" title="Удалить">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <line x1="18" y1="6" x2="6" y2="18"></line>
                        <line x1="6" y1="6" x2="18" y2="18"></line>
                    </svg>
                </button>
            </div>
        `;
    }).join('');
}

/**
 * Remove from favorites
 */
async function removeFavorite(targetId) {
    triggerHaptic('impact', 'medium');
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/favorites/${targetId}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });
        
        if (!response.ok) {
            throw new Error('Failed to remove favorite');
        }
        
        // Reload favorites
        await loadFavorites();
    } catch (error) {
        console.error('Error removing favorite:', error);
    }
}

// ============================================================================
// Match Modal
// ============================================================================

/**
 * Show match modal
 */
function showMatchModal(profile) {
    const modal = document.getElementById('matchModal');
    const matchText = document.getElementById('matchText');
    
    matchText.textContent = `Вы понравились друг другу! Начните общение с ${profile.name}`;
    
    modal.classList.remove('hidden');
}

/**
 * Close match modal
 */
function closeMatchModal() {
    triggerHaptic('impact', 'light');
    
    const modal = document.getElementById('matchModal');
    modal.classList.add('hidden');
}

// ============================================================================
// Utility Functions
// ============================================================================

/**
 * Hide all screens
 */
function hideAllScreens() {
    document.querySelectorAll('.container').forEach(screen => {
        screen.classList.add('hidden');
    });
}

/**
 * Format education
 */
function formatEducation(education) {
    const map = {
        'high_school': 'Среднее',
        'bachelor': 'Бакалавр',
        'master': 'Магистр',
        'phd': 'PhD',
        'other': 'Другое'
    };
    return map[education] || education;
}

/**
 * Format goal
 */
function formatGoal(goal) {
    const map = {
        'friendship': 'Дружба',
        'dating': 'Свидания',
        'relationship': 'Отношения',
        'serious': 'Серьёзные',
        'casual': 'Лёгкое общение',
        'networking': 'Нетворкинг'
    };
    return map[goal] || goal;
}
