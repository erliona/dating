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
    
    // Hide MainButton on discovery screen
    if (tg && tg.MainButton) {
        tg.MainButton.hide();
    }
    
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
    
    // Configure MainButton for profile editing
    setupProfileEditMainButton();
    
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
    
    // Hide MainButton on settings screen
    if (tg && tg.MainButton) {
        tg.MainButton.hide();
    }
    
    // Load settings
    loadSettings();
}

// ============================================================================
// Profile Edit Functions
// ============================================================================

/**
 * Configure MainButton for profile editing
 */
function setupProfileEditMainButton() {
  if (tg && tg.MainButton) {
    tg.MainButton.offClick(handleMainButtonClick); // Remove other handlers
    tg.MainButton.offClick(startProfileCreation);
    tg.MainButton.setText('Сохранить изменения');
    tg.MainButton.show();
    tg.MainButton.enable();
    tg.MainButton.onClick(saveProfileChanges);
  }
}

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
            // Try to get error details from response
            let errorMessage = `HTTP ${response.status}`;
            try {
                const errorData = await response.json();
                errorMessage = errorData.error || errorMessage;
            } catch (e) {
                // Ignore JSON parse errors
            }
            
            console.error('Failed to load profile:', response.status, errorMessage);
            
            // Handle 404 - profile doesn't exist yet
            if (response.status === 404) {
                console.log('Profile not found, redirecting to profile creation');
                hideAllScreens();
                startProfileCreation();
                return;
            }
            
            // Handle 401 - authentication error, try to refresh token
            if (response.status === 401) {
                console.log('Auth token expired or invalid, refreshing...');
                authToken = null; // Clear the invalid token
                authToken = await getAuthToken(); // Get a new token
                
                // Retry the request with new token
                const retryResponse = await fetch(`${API_BASE_URL}/api/profile`, {
                    headers: {
                        'Authorization': `Bearer ${authToken}`
                    }
                });
                
                if (retryResponse.ok) {
                    const data = await retryResponse.json();
                    const profile = data.profile;
                    
                    // Populate basic form fields
                    document.getElementById('editName').value = profile.name || '';
                    document.getElementById('editBio').value = profile.bio || '';
                    document.getElementById('editCity').value = profile.city || '';
                    
                    // Populate optional fields
                    document.getElementById('editHeight').value = profile.height_cm || '';
                    document.getElementById('editEducation').value = profile.education || '';
                    
                    // Handle boolean fields
                    if (profile.has_children !== null && profile.has_children !== undefined) {
                        document.getElementById('editHasChildren').value = String(profile.has_children);
                    } else {
                        document.getElementById('editHasChildren').value = '';
                    }
                    
                    if (profile.wants_children !== null && profile.wants_children !== undefined) {
                        document.getElementById('editWantsChildren').value = String(profile.wants_children);
                    } else {
                        document.getElementById('editWantsChildren').value = '';
                    }
                    
                    if (profile.smoking !== null && profile.smoking !== undefined) {
                        document.getElementById('editSmoking').value = String(profile.smoking);
                    } else {
                        document.getElementById('editSmoking').value = '';
                    }
                    
                    if (profile.drinking !== null && profile.drinking !== undefined) {
                        document.getElementById('editDrinking').value = String(profile.drinking);
                    } else {
                        document.getElementById('editDrinking').value = '';
                    }
                    
                    // Handle interests array
                    if (profile.interests && Array.isArray(profile.interests)) {
                        document.getElementById('editInterests').value = profile.interests.join(', ');
                    } else {
                        document.getElementById('editInterests').value = '';
                    }
                    
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
                    
                    console.log('Profile loaded successfully after token refresh');
                    return;
                }
                
                // If retry also failed, fall through to error handling
                console.error('Retry failed:', retryResponse.status);
            }
            
            throw new Error(`Failed to load profile: ${response.status} - ${errorMessage}`);
        }
        
        const data = await response.json();
        const profile = data.profile;
        
        // Populate basic form fields
        document.getElementById('editName').value = profile.name || '';
        document.getElementById('editBio').value = profile.bio || '';
        document.getElementById('editCity').value = profile.city || '';
        
        // Populate optional fields
        document.getElementById('editHeight').value = profile.height_cm || '';
        document.getElementById('editEducation').value = profile.education || '';
        
        // Handle boolean fields
        if (profile.has_children !== null && profile.has_children !== undefined) {
            document.getElementById('editHasChildren').value = String(profile.has_children);
        } else {
            document.getElementById('editHasChildren').value = '';
        }
        
        if (profile.wants_children !== null && profile.wants_children !== undefined) {
            document.getElementById('editWantsChildren').value = String(profile.wants_children);
        } else {
            document.getElementById('editWantsChildren').value = '';
        }
        
        if (profile.smoking !== null && profile.smoking !== undefined) {
            document.getElementById('editSmoking').value = String(profile.smoking);
        } else {
            document.getElementById('editSmoking').value = '';
        }
        
        if (profile.drinking !== null && profile.drinking !== undefined) {
            document.getElementById('editDrinking').value = String(profile.drinking);
        } else {
            document.getElementById('editDrinking').value = '';
        }
        
        // Handle interests array
        if (profile.interests && Array.isArray(profile.interests)) {
            document.getElementById('editInterests').value = profile.interests.join(', ');
        } else {
            document.getElementById('editInterests').value = '';
        }
        
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
        
        // Prepare update data with basic fields
        const updateData = {
            name: name.trim(),
            bio: bio ? bio.trim() : null,
            city: city ? city.trim() : null
        };
        
        // Add optional fields
        const heightCm = document.getElementById('editHeight').value;
        if (heightCm && heightCm.trim() !== '') {
            updateData.height_cm = parseInt(heightCm);
        } else {
            updateData.height_cm = null;
        }
        
        const education = document.getElementById('editEducation').value;
        if (education && education.trim() !== '') {
            updateData.education = education;
        } else {
            updateData.education = null;
        }
        
        // Handle boolean fields
        const hasChildren = document.getElementById('editHasChildren').value;
        if (hasChildren && hasChildren.trim() !== '') {
            updateData.has_children = hasChildren === 'true';
        } else {
            updateData.has_children = null;
        }
        
        const wantsChildren = document.getElementById('editWantsChildren').value;
        if (wantsChildren && wantsChildren.trim() !== '') {
            updateData.wants_children = wantsChildren === 'true';
        } else {
            updateData.wants_children = null;
        }
        
        const smoking = document.getElementById('editSmoking').value;
        if (smoking && smoking.trim() !== '') {
            updateData.smoking = smoking === 'true';
        } else {
            updateData.smoking = null;
        }
        
        const drinking = document.getElementById('editDrinking').value;
        if (drinking && drinking.trim() !== '') {
            updateData.drinking = drinking === 'true';
        } else {
            updateData.drinking = null;
        }
        
        // Handle interests array
        const interests = document.getElementById('editInterests').value;
        if (interests && interests.trim() !== '') {
            updateData.interests = interests.split(',').map(i => i.trim()).filter(i => i);
        } else {
            updateData.interests = null;
        }
        
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
