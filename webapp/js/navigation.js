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
        // In a real app, fetch profile from API
        // For now, just placeholder
        console.log('Loading profile for edit');
    } catch (error) {
        console.error('Error loading profile:', error);
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
        // In a real app, send to API
        // For now, just show success message
        if (tg && tg.showAlert) {
            tg.showAlert('Изменения сохранены ✓');
        }
        
        triggerHaptic('notification', 'success');
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
