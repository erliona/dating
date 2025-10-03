/**
 * Bottom Navigation functionality
 */

// ============================================================================
// Navigation Functions
// ============================================================================

/**
 * Show bottom navigation
 */
function showBottomNav() {
    const nav = document.getElementById('bottom-nav');
    if (nav) {
        nav.classList.remove('hidden');
    }
}

/**
 * Hide bottom navigation
 */
function hideBottomNav() {
    const nav = document.getElementById('bottom-nav');
    if (nav) {
        nav.classList.add('hidden');
    }
}

/**
 * Set active tab in navigation
 */
function setActiveTab(tabName) {
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(item => {
        if (item.dataset.tab === tabName) {
            item.classList.add('active');
        } else {
            item.classList.remove('active');
        }
    });
}

/**
 * Show discovery from navigation
 */
function showDiscoveryFromNav() {
    hideAllScreens();
    document.getElementById('discovery-screen').classList.remove('hidden');
    showBottomNav();
    setActiveTab('discovery');
    triggerHaptic('impact', 'light');
    
    // Load cards if needed
    if (currentCards.length === 0) {
        loadDiscoveryCards();
    }
    updateMatchesBadge();
}

/**
 * Show profile edit screen
 */
function showProfileEdit() {
    hideAllScreens();
    document.getElementById('profile-edit-screen').classList.remove('hidden');
    showBottomNav();
    setActiveTab('profile');
    triggerHaptic('impact', 'light');
    
    // Load current profile data
    loadProfileForEdit();
}

/**
 * Show settings screen
 */
function showSettings() {
    hideAllScreens();
    document.getElementById('settings-screen').classList.remove('hidden');
    showBottomNav();
    setActiveTab('settings');
    triggerHaptic('impact', 'light');
    
    // Load settings
    loadSettings();
}

// ============================================================================
// Profile Edit Functions
// ============================================================================

/**
 * Load profile data for editing
 */
async function loadProfileForEdit() {
    try {
        console.log('Loading profile for edit');
        
        // Get or generate JWT token
        if (!authToken) {
            console.log('No auth token, generating one...');
            authToken = await getAuthToken();
        }
        
        // Fetch profile from API
        const response = await fetch(`${API_BASE_URL}/api/profile`, {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });
        
        if (!response.ok) {
            throw new Error(`Failed to load profile: ${response.status}`);
        }
        
        const data = await response.json();
        const profile = data.profile;
        
        // Populate form fields
        document.getElementById('editName').value = profile.name || '';
        document.getElementById('editBio').value = profile.bio || '';
        document.getElementById('editCity').value = profile.city || '';
        
        // Load photos if available
        if (profile.photos && profile.photos.length > 0) {
            profile.photos.forEach((photo, index) => {
                const photoSlot = document.getElementById(`editPhotoSlot${index}`);
                if (photoSlot && photo.url) {
                    photoSlot.style.backgroundImage = `url(${photo.url})`;
                    photoSlot.style.backgroundSize = 'cover';
                    photoSlot.style.backgroundPosition = 'center';
                    photoSlot.querySelector('span').style.display = 'none';
                }
            });
        }
        
        console.log('Profile loaded successfully');
    } catch (error) {
        console.error('Error loading profile:', error);
        if (tg && tg.showAlert) {
            tg.showAlert('Не удалось загрузить профиль');
        }
    }
}

/**
 * Save profile changes
 */
async function saveProfileChanges() {
    triggerHaptic('impact', 'medium');
    
    const name = document.getElementById('editName').value;
    const bio = document.getElementById('editBio').value;
    const city = document.getElementById('editCity').value;
    
    try {
        // Validate required fields
        if (!name || name.trim().length < 2) {
            if (tg && tg.showAlert) {
                tg.showAlert('Имя должно содержать минимум 2 символа');
            }
            return;
        }
        
        // Get or generate JWT token
        if (!authToken) {
            console.log('No auth token, generating one...');
            authToken = await getAuthToken();
        }
        
        // Prepare update data
        const updateData = {
            name: name.trim(),
            bio: bio ? bio.trim() : null,
            city: city ? city.trim() : null
        };
        
        // Send to API
        const response = await fetch(`${API_BASE_URL}/api/profile`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify(updateData)
        });
        
        if (!response.ok) {
            throw new Error(`Failed to update profile: ${response.status}`);
        }
        
        const result = await response.json();
        
        if (result.success) {
            if (tg && tg.showAlert) {
                tg.showAlert('Изменения сохранены ✓');
            }
            triggerHaptic('notification', 'success');
            
            // Update localStorage if profile data is cached
            const storedProfile = localStorage.getItem('profile_data');
            if (storedProfile) {
                try {
                    const profileData = JSON.parse(storedProfile);
                    profileData.name = updateData.name;
                    profileData.bio = updateData.bio;
                    profileData.city = updateData.city;
                    localStorage.setItem('profile_data', JSON.stringify(profileData));
                } catch (e) {
                    console.warn('Failed to update cached profile:', e);
                }
            }
        } else {
            throw new Error('Update failed');
        }
    } catch (error) {
        console.error('Error saving profile:', error);
        
        if (tg && tg.showAlert) {
            tg.showAlert('Ошибка при сохранении');
        }
    }
}

// ============================================================================
// Settings Functions
// ============================================================================

/**
 * Load settings
 */
function loadSettings() {
    // Load saved settings from localStorage or API
    const hideAge = localStorage.getItem('hideAge') === 'true';
    const hideDistance = localStorage.getItem('hideDistance') === 'true';
    const notifyMatches = localStorage.getItem('notifyMatches') !== 'false';
    const notifyMessages = localStorage.getItem('notifyMessages') !== 'false';
    
    document.getElementById('hideAge').checked = hideAge;
    document.getElementById('hideDistance').checked = hideDistance;
    document.getElementById('notifyMatches').checked = notifyMatches;
    document.getElementById('notifyMessages').checked = notifyMessages;
    
    // Add change listeners
    document.getElementById('hideAge').addEventListener('change', saveSetting);
    document.getElementById('hideDistance').addEventListener('change', saveSetting);
    document.getElementById('notifyMatches').addEventListener('change', saveSetting);
    document.getElementById('notifyMessages').addEventListener('change', saveSetting);
}

/**
 * Save individual setting
 */
function saveSetting(event) {
    const settingId = event.target.id;
    const value = event.target.checked;
    
    localStorage.setItem(settingId, value);
    triggerHaptic('impact', 'light');
    
    console.log(`Setting ${settingId} changed to ${value}`);
}

// ============================================================================
// Override showDiscovery to show nav
// ============================================================================

// Store original showDiscovery
const originalShowDiscovery = typeof showDiscovery !== 'undefined' ? showDiscovery : null;

// Override to include nav
if (originalShowDiscovery) {
    window.showDiscovery = function() {
        originalShowDiscovery();
        showBottomNav();
        setActiveTab('discovery');
    };
}

// ============================================================================
// Initialization
// ============================================================================

// Show bottom nav after profile is complete
document.addEventListener('DOMContentLoaded', () => {
    // Check if user has completed profile
    const hasProfile = localStorage.getItem('hasProfile');
    if (hasProfile === 'true') {
        showBottomNav();
    }
});
