/**
 * Dating Mini App - Telegram WebApp Integration
 * Epic A1: Mini App initialization and bridge to Telegram WebApp API
 */

// ============================================================================
// Telegram WebApp Integration
// ============================================================================

let tg = null;
let initData = null;
let uploadedPhotos = [];
let uploadProgress = [0, 0, 0]; // Track upload progress for each slot
let authToken = null; // JWT token for API authentication

// App version for cache invalidation
const APP_VERSION = '1.2.0'; // Updated for HTTP upload feature

// API configuration
const API_BASE_URL = window.location.protocol + '//' + window.location.hostname + ':8080';

/**
 * Initialize Telegram WebApp
 */
function initTelegramWebApp() {
  if (!window.Telegram || !window.Telegram.WebApp) {
    console.error('Telegram WebApp SDK not loaded');
    showError('This app can only be opened in Telegram');
    return false;
  }

  tg = window.Telegram.WebApp;
  
  // Expand the app to full height
  tg.expand();
  
  // Enable closing confirmation
  tg.enableClosingConfirmation();
  
  // Get init data for authentication
  initData = tg.initData;
  
  // Set up BackButton handler
  tg.BackButton.onClick(() => {
    handleBackButton();
  });
  
  console.log('Telegram WebApp initialized', {
    version: tg.version,
    platform: tg.platform,
    colorScheme: tg.colorScheme,
    initDataUnsafe: tg.initDataUnsafe
  });
  
  return true;
}

/**
 * Handle BackButton click
 */
function handleBackButton() {
  // Provide haptic feedback
  triggerHaptic('impact', 'medium');
  
  // In a real app, this would navigate back in the app
  // For demo, we just hide the back button
  tg.BackButton.hide();
  
  console.log('Back button clicked');
}

/**
 * Show BackButton
 */
function showBackButton() {
  if (tg) {
    tg.BackButton.show();
  }
}

/**
 * Hide BackButton
 */
function hideBackButton() {
  if (tg) {
    tg.BackButton.hide();
  }
}

// ============================================================================
// Theme Handling
// ============================================================================

/**
 * Apply Telegram theme colors to CSS variables
 */
function applyTheme() {
  if (!tg) return;
  
  const themeParams = tg.themeParams;
  const root = document.documentElement;
  
  // Map Telegram theme parameters to CSS variables
  const themeMap = {
    'bg_color': '--tg-theme-bg-color',
    'text_color': '--tg-theme-text-color',
    'hint_color': '--tg-theme-hint-color',
    'link_color': '--tg-theme-link-color',
    'button_color': '--tg-theme-button-color',
    'button_text_color': '--tg-theme-button-text-color',
    'secondary_bg_color': '--tg-theme-secondary-bg-color'
  };
  
  // Apply theme colors
  for (const [tgParam, cssVar] of Object.entries(themeMap)) {
    if (themeParams[tgParam]) {
      root.style.setProperty(cssVar, themeParams[tgParam]);
    }
  }
  
  console.log('Theme applied', {
    colorScheme: tg.colorScheme,
    themeParams: themeParams
  });
  
  // Update theme demo
  updateThemeDemo();
}

/**
 * Listen for theme changes
 */
function setupThemeListener() {
  if (!tg) return;
  
  tg.onEvent('themeChanged', () => {
    console.log('Theme changed to:', tg.colorScheme);
    applyTheme();
    triggerHaptic('impact', 'light');
  });
}

/**
 * Update theme demo display
 */
function updateThemeDemo() {
  if (!tg) return;
  
  const colors = [
    { name: 'Background', var: '--tg-theme-bg-color', key: 'bg_color' },
    { name: 'Text', var: '--tg-theme-text-color', key: 'text_color' },
    { name: 'Hint', var: '--tg-theme-hint-color', key: 'hint_color' },
    { name: 'Link', var: '--tg-theme-link-color', key: 'link_color' },
    { name: 'Button', var: '--tg-theme-button-color', key: 'button_color' },
    { name: 'Button Text', var: '--tg-theme-button-text-color', key: 'button_text_color' },
    { name: 'Secondary BG', var: '--tg-theme-secondary-bg-color', key: 'secondary_bg_color' }
  ];
  
  const container = document.getElementById('themeColors');
  if (!container) return;
  
  container.innerHTML = colors.map(color => {
    const value = tg.themeParams[color.key] || 
                  getComputedStyle(document.documentElement).getPropertyValue(color.var);
    
    return `
      <div class="color-card">
        <div class="color-sample" style="background-color: ${value}"></div>
        <div class="color-name">${color.name}</div>
        <div class="color-value">${value}</div>
      </div>
    `;
  }).join('');
}

// ============================================================================
// Haptic Feedback
// ============================================================================

/**
 * Trigger haptic feedback
 * @param {string} type - 'impact', 'notification', or 'selection'
 * @param {string} style - For impact: 'light', 'medium', 'heavy', 'rigid', 'soft'
 *                         For notification: 'error', 'success', 'warning'
 */
function triggerHaptic(type = 'impact', style = 'medium') {
  if (!tg || !tg.HapticFeedback) {
    console.warn('Haptic feedback not available');
    return;
  }
  
  try {
    switch (type) {
      case 'impact':
        tg.HapticFeedback.impactOccurred(style);
        break;
      case 'notification':
        tg.HapticFeedback.notificationOccurred(style);
        break;
      case 'selection':
        tg.HapticFeedback.selectionChanged();
        break;
      default:
        console.warn('Unknown haptic type:', type);
    }
  } catch (error) {
    console.error('Haptic feedback error:', error);
  }
}

// ============================================================================
// UI State Management
// ============================================================================

/**
 * Show loading state
 */
function showLoading() {
  const loading = document.getElementById('loading');
  const content = document.getElementById('content');
  
  if (loading) loading.classList.remove('hidden');
  if (content) content.classList.add('hidden');
}

/**
 * Show main content
 */
function showContent() {
  const loading = document.getElementById('loading');
  const content = document.getElementById('content');
  
  if (loading) loading.classList.add('hidden');
  if (content) content.classList.remove('hidden');
}

/**
 * Show error state
 */
function showError(message) {
  const content = document.getElementById('content');
  if (!content) return;
  
  content.innerHTML = `
    <div class="info-card text-center">
      <h2>❌ Error</h2>
      <p>${message}</p>
    </div>
  `;
  showContent();
}

// ============================================================================
// Platform Information
// ============================================================================

/**
 * Get platform information
 */
function getPlatformInfo() {
  if (!tg) return null;
  
  return {
    platform: tg.platform,
    version: tg.version,
    colorScheme: tg.colorScheme,
    isExpanded: tg.isExpanded,
    viewportHeight: tg.viewportHeight,
    viewportStableHeight: tg.viewportStableHeight,
    headerColor: tg.headerColor,
    backgroundColor: tg.backgroundColor,
    isClosingConfirmationEnabled: tg.isClosingConfirmationEnabled
  };
}

/**
 * Display platform information
 */
function displayPlatformInfo() {
  const info = getPlatformInfo();
  if (!info) return;
  
  const container = document.getElementById('platformInfo');
  if (!container) return;
  
  container.innerHTML = `
    <ul class="info-list">
      <li><strong>Platform:</strong> ${info.platform}</li>
      <li><strong>Version:</strong> ${info.version}</li>
      <li><strong>Color Scheme:</strong> ${info.colorScheme}</li>
      <li><strong>Viewport Height:</strong> ${info.viewportHeight}px</li>
      <li><strong>Stable Height:</strong> ${info.viewportStableHeight}px</li>
      <li><strong>Expanded:</strong> ${info.isExpanded ? '✅' : '❌'}</li>
      <li><strong>Close Confirmation:</strong> ${info.isClosingConfirmationEnabled ? '✅' : '❌'}</li>
    </ul>
  `;
}

// ============================================================================
// Deep Links (A3)
// ============================================================================

/**
 * Parse start parameter from URL or initData
 */
function parseStartParam() {
  if (!tg || !tg.initDataUnsafe) return null;
  
  const startParam = tg.initDataUnsafe.start_param;
  
  if (startParam) {
    console.log('Start parameter detected:', startParam);
    return startParam;
  }
  
  return null;
}

/**
 * Handle deep link routing
 * @param {string} param - Start parameter from deep link
 */
function handleDeepLink(param) {
  if (!param) return;
  
  // Parse the parameter format: <type>_<id>
  // Examples: chat_123, profile_456, payment_789
  const [type, id] = param.split('_');
  
  console.log('Deep link routing:', { type, id });
  
  // Trigger haptic feedback for navigation
  triggerHaptic('impact', 'light');
  
  // Route to appropriate screen based on type
  switch (type) {
    case 'chat':
      routeToChat(id);
      break;
    case 'profile':
      routeToProfile(id);
      break;
    case 'payment':
      routeToPayment(id);
      break;
    default:
      console.warn('Unknown deep link type:', type);
  }
}

/**
 * Route to chat screen
 */
function routeToChat(chatId) {
  console.log('Routing to chat:', chatId);
  showInfo('Chat Screen', `Opening chat with ID: ${chatId}`, 'success');
  showBackButton();
}

/**
 * Route to profile screen
 */
function routeToProfile(profileId) {
  console.log('Routing to profile:', profileId);
  showInfo('Profile Screen', `Opening profile with ID: ${profileId}`, 'success');
  showBackButton();
}

/**
 * Route to payment screen
 */
function routeToPayment(paymentId) {
  console.log('Routing to payment:', paymentId);
  showInfo('Payment Screen', `Processing payment with ID: ${paymentId}`, 'success');
  showBackButton();
}

/**
 * Show info message
 */
function showInfo(title, message, type = 'success') {
  const content = document.getElementById('content');
  if (!content) return;
  
  const badge = `<span class="status-badge ${type}">${type}</span>`;
  
  content.innerHTML = `
    <div class="info-card text-center">
      <h2>${title}</h2>
      ${badge}
      <p class="mt-lg">${message}</p>
      <div class="button-group">
        <button class="button" onclick="location.reload()">Back to Home</button>
      </div>
    </div>
  `;
}

// ============================================================================
// Event Handlers
// ============================================================================

/**
 * Test haptic feedback
 */
function testHaptic(type, style) {
  triggerHaptic(type, style);
  console.log('Haptic test:', type, style);
}

/**
 * Test theme toggle (for demo purposes)
 */
function testThemeToggle() {
  // This is just for demo - real theme changes come from Telegram
  console.log('Theme toggle requested - use Telegram app settings to change theme');
  triggerHaptic('notification', 'warning');
}

// ============================================================================
// Onboarding Flow
// ============================================================================

/**
 * Check if user has a profile
 */
async function checkUserProfile() {
  // Get current user ID
  const currentUserId = tg?.initDataUnsafe?.user?.id;
  
  if (!currentUserId) {
    console.warn('No user ID available, cannot check profile');
    return false;
  }
  
  // Check localStorage for quick result
  const profileCreated = localStorage.getItem('profile_created') === 'true';
  const storedUserId = localStorage.getItem('profile_user_id');
  
  // If user IDs don't match, clear the old profile data
  if (profileCreated && storedUserId && storedUserId !== String(currentUserId)) {
    console.log('User ID mismatch, clearing old profile data');
    localStorage.removeItem('profile_created');
    localStorage.removeItem('profile_data');
    localStorage.removeItem('profile_user_id');
  }
  
  // ALWAYS verify with backend API to ensure database has the profile
  // This is the source of truth, not localStorage
  try {
    const response = await fetch(`${API_BASE_URL}/api/profile/check?user_id=${currentUserId}`);
    
    if (!response.ok) {
      console.error('Profile check API failed:', response.status);
      // If API fails, trust localStorage as fallback
      return profileCreated;
    }
    
    const data = await response.json();
    const hasProfileInDB = data.has_profile;
    
    // Sync localStorage with database state
    if (hasProfileInDB && !profileCreated) {
      // Profile exists in DB but not in localStorage - update localStorage
      console.log('Profile found in database, updating localStorage');
      localStorage.setItem('profile_created', 'true');
      localStorage.setItem('profile_user_id', String(currentUserId));
    } else if (!hasProfileInDB && profileCreated) {
      // Profile doesn't exist in DB but localStorage says it does - clear localStorage
      console.log('Profile not found in database, clearing localStorage');
      localStorage.removeItem('profile_created');
      localStorage.removeItem('profile_data');
      localStorage.removeItem('profile_user_id');
    }
    
    return hasProfileInDB;
  } catch (error) {
    console.error('Error checking profile with API:', error);
    // If API call fails, trust localStorage as fallback
    return profileCreated;
  }
}

/**
 * Update version text on all pages
 */
function updateVersionText() {
  const versionElements = [
    'appVersionText',
    'appVersionTextForm',
    'appVersionTextSuccess'
  ];
  
  versionElements.forEach(id => {
    const el = document.getElementById(id);
    if (el) {
      el.textContent = APP_VERSION;
    }
  });
}

/**
 * Show onboarding screen (Welcome)
 */
function showOnboarding() {
  document.getElementById('loading').classList.add('hidden');
  document.getElementById('onboarding').classList.remove('hidden');
  document.getElementById('profile-form').classList.add('hidden');
  document.getElementById('success-screen').classList.add('hidden');
  
  // Set version text on all pages
  updateVersionText();
  
  // Haptic feedback
  triggerHaptic('impact', 'light');
}

/**
 * Start profile creation (Step 2: Registration Form)
 */
function startProfileCreation() {
  document.getElementById('onboarding').classList.add('hidden');
  document.getElementById('profile-form').classList.remove('hidden');
  
  // Set version text on all pages
  updateVersionText();
  
  triggerHaptic('notification', 'success');
}

/**
 * Show success screen
 */
function showSuccessScreen() {
  document.getElementById('loading').classList.add('hidden');
  document.getElementById('onboarding').classList.add('hidden');
  document.getElementById('profile-form').classList.add('hidden');
  document.getElementById('success-screen').classList.remove('hidden');
  
  // Set version text on all pages
  updateVersionText();
  
  // Mark that user has profile
  localStorage.setItem('hasProfile', 'true');
  
  triggerHaptic('notification', 'success');
}

// ============================================================================
// Geolocation Detection
// ============================================================================

/**
 * Detect user location using sequential fallback:
 * 1. Telegram WebApp API
 * 2. Browser Geolocation API
 * 3. IP-based geolocation
 */
async function detectUserLocation() {
  const statusEl = document.getElementById('locationStatus');
  const detectBtn = document.getElementById('detectLocationBtn');
  const cityInput = document.getElementById('cityInput');
  const latInput = document.getElementById('latitude');
  const lonInput = document.getElementById('longitude');
  
  if (!statusEl || !detectBtn) return;
  
  // Haptic feedback when starting location detection
  triggerHaptic('impact', 'medium');
  
  // Show detecting status
  statusEl.className = 'location-status detecting';
  statusEl.textContent = '🔍 Определяем ваше местоположение...';
  statusEl.classList.remove('hidden');
  detectBtn.disabled = true;
  
  try {
    // 1. Try Telegram's location API first
    if (tg && tg.LocationManager) {
      try {
        const location = await tg.LocationManager.getLocation();
        if (location && location.latitude && location.longitude) {
          await handleLocationSuccess(location.latitude, location.longitude);
          return;
        }
      } catch (e) {
        console.log('Telegram location not available, trying browser API');
      }
    }
    
    // 2. Fallback to browser geolocation API
    if ('geolocation' in navigator) {
      try {
        const position = await new Promise((resolve, reject) => {
          navigator.geolocation.getCurrentPosition(
            resolve,
            reject,
            {
              enableHighAccuracy: true,
              timeout: 15000,
              maximumAge: 0
            }
          );
        });
        
        await handleLocationSuccess(
          position.coords.latitude,
          position.coords.longitude
        );
        return;
      } catch (error) {
        console.log('Browser geolocation failed, trying IP-based location');
      }
    }
    
    // 3. Final fallback: IP-based geolocation
    await detectLocationByIP();
    
  } catch (error) {
    handleLocationError(error);
  }
}

/**
 * Detect location by IP address (fallback method)
 */
async function detectLocationByIP() {
  const statusEl = document.getElementById('locationStatus');
  const detectBtn = document.getElementById('detectLocationBtn');
  const cityInput = document.getElementById('cityInput');
  const latInput = document.getElementById('latitude');
  const lonInput = document.getElementById('longitude');
  
  try {
    // Use ipapi.co for IP-based geolocation
    const response = await fetch('https://ipapi.co/json/');
    
    if (!response.ok) {
      throw new Error('IP geolocation service unavailable');
    }
    
    const data = await response.json();
    
    if (data.latitude && data.longitude) {
      await handleLocationSuccess(data.latitude, data.longitude);
    } else {
      throw new Error('Could not determine location from IP');
    }
  } catch (error) {
    console.error('IP-based location detection failed:', error);
    handleLocationError(new Error('Не удалось определить местоположение. Укажите город вручную.'));
  }
}

/**
 * Handle successful location detection
 */
async function handleLocationSuccess(latitude, longitude) {
  const statusEl = document.getElementById('locationStatus');
  const detectBtn = document.getElementById('detectLocationBtn');
  const cityInput = document.getElementById('cityInput');
  const latInput = document.getElementById('latitude');
  const lonInput = document.getElementById('longitude');
  
  // Store coordinates
  latInput.value = latitude;
  lonInput.value = longitude;
  
  // Try to reverse geocode to get city name
  try {
    const city = await reverseGeocode(latitude, longitude);
    if (city) {
      cityInput.value = city;
      cityInput.readOnly = true;
    }
    
    statusEl.className = 'location-status success';
    statusEl.textContent = `✅ Местоположение определено: ${city || 'координаты сохранены'}`;
    
    triggerHaptic('notification', 'success');
  } catch (error) {
    console.error('Reverse geocoding failed:', error);
    statusEl.className = 'location-status success';
    statusEl.textContent = '✅ Координаты сохранены. Укажите город вручную.';
    cityInput.readOnly = false;
  }
  
  detectBtn.disabled = false;
  detectBtn.textContent = '🔄 Определить заново';
}

/**
 * Handle location detection error
 */
function handleLocationError(error) {
  const statusEl = document.getElementById('locationStatus');
  const detectBtn = document.getElementById('detectLocationBtn');
  const cityInput = document.getElementById('cityInput');
  
  console.error('Location detection error:', error);
  
  statusEl.className = 'location-status error';
  statusEl.textContent = '❌ Не удалось определить местоположение. Укажите город вручную.';
  
  cityInput.readOnly = false;
  cityInput.focus();
  
  detectBtn.disabled = false;
  
  triggerHaptic('notification', 'error');
}

/**
 * Reverse geocode coordinates to city name
 */
async function reverseGeocode(latitude, longitude) {
  // Use Nominatim (OpenStreetMap) for reverse geocoding
  try {
    const response = await fetch(
      `https://nominatim.openstreetmap.org/reverse?format=json&lat=${latitude}&lon=${longitude}&zoom=10&addressdetails=1`,
      {
        headers: {
          'User-Agent': 'DatingMiniApp/1.0'
        }
      }
    );
    
    if (!response.ok) {
      throw new Error('Geocoding failed');
    }
    
    const data = await response.json();
    
    // Try to extract city name from various fields
    const address = data.address || {};
    const city = address.city || 
                 address.town || 
                 address.village || 
                 address.municipality ||
                 address.county ||
                 address.state;
    
    return city || null;
  } catch (error) {
    console.error('Reverse geocoding error:', error);
    return null;
  }
}

// ============================================================================
// Photo Upload
// ============================================================================

/**
 * Setup photo upload handlers
 */
function setupPhotoUpload() {
  // Setup individual file inputs for each slot
  for (let i = 0; i < 3; i++) {
    const input = document.getElementById(`photoInput${i}`);
    
    if (input) {
      input.addEventListener('change', async (e) => {
        // Trigger haptic feedback when file is selected (not on click)
        // This avoids interfering with iOS file picker
        if (e.target.files && e.target.files[0]) {
          triggerHaptic('impact', 'light');
          
          // Handle the upload
          await handlePhotoUpload(e.target.files[0], i);
          
          // Reset input to allow selecting the same file again
          e.target.value = '';
        }
      });
    }
    
    // Don't add click handlers to photo slots on iOS
    // The label's native behavior handles the click → file input trigger
    // Additional handlers can interfere with iOS Safari's file picker
  }
}

/**
 * Handle photo upload for a specific slot
 */
async function handlePhotoUpload(file, slotIndex) {
  if (!file) return;
  
  // Validate file
  if (!file.type.startsWith('image/')) {
    showFormError('Пожалуйста, выберите изображение');
    return;
  }
  
  if (file.size > 5 * 1024 * 1024) {
    showFormError('Файл слишком большой. Максимум 5 МБ');
    return;
  }
  
  // First, show preview locally
  const reader = new FileReader();
  reader.onload = async (e) => {
    uploadedPhotos[slotIndex] = e.target.result;
    updatePhotoSlot(slotIndex, e.target.result);
    updatePhotoCounter();
    
    // Show upload progress
    showUploadProgress(slotIndex, 0);
    
    // Try to upload to server via HTTP API
    try {
      await uploadPhotoToServer(file, slotIndex);
    } catch (error) {
      console.error('HTTP upload failed, keeping local copy:', error);
      // Keep local copy even if upload fails
      triggerHaptic('notification', 'warning');
    }
  };
  
  reader.readAsDataURL(file);
}

/**
 * Upload photo to server via HTTP API with progress tracking
 */
async function uploadPhotoToServer(file, slotIndex) {
  try {
    // Get or generate auth token
    if (!authToken) {
      authToken = await getAuthToken();
    }
    
    // Create form data
    const formData = new FormData();
    formData.append('photo', file);
    formData.append('slot_index', slotIndex);
    
    // Create XMLHttpRequest for progress tracking
    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();
      
      // Track upload progress
      xhr.upload.addEventListener('progress', (e) => {
        if (e.lengthComputable) {
          const percentComplete = (e.loaded / e.total) * 100;
          uploadProgress[slotIndex] = percentComplete;
          showUploadProgress(slotIndex, percentComplete);
        }
      });
      
      // Handle completion
      xhr.addEventListener('load', () => {
        if (xhr.status === 200) {
          const response = JSON.parse(xhr.responseText);
          console.log('Photo uploaded successfully:', response);
          showUploadProgress(slotIndex, 100);
          triggerHaptic('notification', 'success');
          
          // Hide progress after 1 second
          setTimeout(() => hideUploadProgress(slotIndex), 1000);
          
          resolve(response);
        } else {
          const error = JSON.parse(xhr.responseText);
          console.error('Upload failed:', error);
          hideUploadProgress(slotIndex);
          reject(new Error(error.error || 'Upload failed'));
        }
      });
      
      // Handle errors
      xhr.addEventListener('error', () => {
        console.error('Upload error');
        hideUploadProgress(slotIndex);
        reject(new Error('Network error'));
      });
      
      // Send request
      xhr.open('POST', `${API_BASE_URL}/api/photos/upload`);
      xhr.setRequestHeader('Authorization', `Bearer ${authToken}`);
      xhr.send(formData);
    });
  } catch (error) {
    console.error('Upload to server failed:', error);
    hideUploadProgress(slotIndex);
    throw error;
  }
}

/**
 * Get authentication token for API
 */
async function getAuthToken() {
  try {
    // Extract user ID from Telegram data
    const userId = tg?.initDataUnsafe?.user?.id || 12345; // Default for testing
    
    const response = await fetch(`${API_BASE_URL}/api/auth/token`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ user_id: userId })
    });
    
    if (!response.ok) {
      throw new Error('Failed to get auth token');
    }
    
    const data = await response.json();
    return data.token;
  } catch (error) {
    console.error('Failed to get auth token:', error);
    throw error;
  }
}

/**
 * Show upload progress indicator
 */
function showUploadProgress(slotIndex, percent) {
  const slot = document.getElementById(`photoSlot${slotIndex}`);
  if (!slot) return;
  
  // Find or create progress bar
  let progressBar = slot.querySelector('.upload-progress');
  if (!progressBar) {
    progressBar = document.createElement('div');
    progressBar.className = 'upload-progress';
    progressBar.innerHTML = `
      <div class="progress-bar">
        <div class="progress-fill"></div>
      </div>
      <div class="progress-text">Загрузка...</div>
    `;
    slot.appendChild(progressBar);
  }
  
  // Update progress
  const progressFill = progressBar.querySelector('.progress-fill');
  const progressText = progressBar.querySelector('.progress-text');
  if (progressFill) {
    progressFill.style.width = `${percent}%`;
  }
  if (progressText) {
    progressText.textContent = percent >= 100 ? 'Готово!' : `Загрузка ${Math.round(percent)}%`;
  }
  
  progressBar.style.display = 'block';
}

/**
 * Hide upload progress indicator
 */
function hideUploadProgress(slotIndex) {
  const slot = document.getElementById(`photoSlot${slotIndex}`);
  if (!slot) return;
  
  const progressBar = slot.querySelector('.upload-progress');
  if (progressBar) {
    progressBar.style.display = 'none';
  }
}

/**
 * Update a specific photo slot
 */
function updatePhotoSlot(slotIndex, photoData) {
  const slot = document.getElementById(`photoSlot${slotIndex}`);
  const input = document.getElementById(`photoInput${slotIndex}`);
  if (!slot) return;
  
  if (photoData) {
    // Add photo - find or create img element
    let img = slot.querySelector('img');
    if (!img) {
      img = document.createElement('img');
      slot.appendChild(img);
    }
    img.src = photoData;
    img.alt = `Фото ${slotIndex + 1}`;
    
    // Add or update remove button
    let removeBtn = slot.querySelector('.remove-photo');
    if (!removeBtn) {
      removeBtn = document.createElement('button');
      removeBtn.className = 'remove-photo';
      removeBtn.textContent = '×';
      removeBtn.type = 'button';
      removeBtn.onclick = (e) => {
        e.preventDefault();
        e.stopPropagation();
        removePhoto(slotIndex);
      };
      slot.appendChild(removeBtn);
    }
    
    // Hide the content placeholder
    const content = slot.querySelector('.photo-slot-content');
    if (content) {
      content.style.display = 'none';
    }
    
    slot.classList.add('has-photo');
  } else {
    // Remove photo - show placeholder
    const img = slot.querySelector('img');
    if (img) img.remove();
    
    const removeBtn = slot.querySelector('.remove-photo');
    if (removeBtn) removeBtn.remove();
    
    // Show the content placeholder
    const content = slot.querySelector('.photo-slot-content');
    if (content) {
      content.style.display = 'flex';
    }
    
    slot.classList.remove('has-photo');
  }
}

/**
 * Update photo counter
 */
function updatePhotoCounter() {
  const counter = document.getElementById('photoCount');
  if (!counter) return;
  
  const count = uploadedPhotos.filter(photo => photo).length;
  counter.textContent = count;
}

/**
 * Remove photo from specific slot
 */
function removePhoto(slotIndex) {
  uploadedPhotos[slotIndex] = null;
  updatePhotoSlot(slotIndex, null);
  updatePhotoCounter();
  triggerHaptic('impact', 'light');
}

// ============================================================================
// Profile Form
// ============================================================================

/**
 * Setup profile form handler
 */
function setupProfileForm() {
  const form = document.getElementById('profileForm');
  if (!form) return;
  
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    await handleProfileSubmit(e.target);
  });
}

/**
 * Handle profile form submission
 */
async function handleProfileSubmit(form) {
  // Haptic feedback on form submission attempt
  triggerHaptic('impact', 'medium');
  
  // Validate photos (must have exactly 3)
  const validPhotos = uploadedPhotos.filter(photo => photo);
  if (validPhotos.length !== 3) {
    showFormError('Требуется ровно 3 фотографии');
    return;
  }
  
  const formData = new FormData(form);
  const profileData = {
    name: formData.get('name'),
    birth_date: formData.get('birth_date'),
    gender: formData.get('gender'),
    orientation: formData.get('orientation'),
    goal: formData.get('goal'),
    bio: formData.get('bio') || '',
    city: formData.get('city') || ''
  };
  
  // Validate city is provided
  if (!profileData.city || profileData.city.trim() === '') {
    showFormError('Укажите город');
    return;
  }
  
  // Validate age (18+)
  const birthDate = new Date(profileData.birth_date);
  const today = new Date();
  const age = today.getFullYear() - birthDate.getFullYear();
  const monthDiff = today.getMonth() - birthDate.getMonth();
  
  if (age < 18 || (age === 18 && monthDiff < 0)) {
    showFormError('Вам должно быть не менее 18 лет');
    return;
  }
  
  // Add photos (filter out nulls)
  profileData.photos = uploadedPhotos.filter(photo => photo);
  
  // Add geolocation data if available
  const latitude = formData.get('latitude');
  const longitude = formData.get('longitude');
  
  if (latitude && longitude) {
    profileData.latitude = parseFloat(latitude);
    profileData.longitude = parseFloat(longitude);
    
    // Calculate geohash for privacy-preserving location storage
    profileData.geohash = calculateGeohash(
      profileData.latitude, 
      profileData.longitude,
      5 // precision ~5km for matching
    );
    
    console.log('Location data:', {
      city: profileData.city,
      lat: profileData.latitude,
      lon: profileData.longitude,
      geohash: profileData.geohash
    });
  } else {
    console.log('No GPS coordinates, using city only:', profileData.city);
  }
  
  try {
    // Send data to Telegram bot
    if (tg && tg.sendData) {
      // Note: tg.sendData() has a 4096-byte limit, so we can't send photos directly
      // Photos should be uploaded via HTTP API separately
      // For now, we only send profile metadata and store photos locally
      
      // Prepare payload without photos (to avoid exceeding size limit)
      const profileMetadata = {
        name: profileData.name,
        birth_date: profileData.birth_date,
        gender: profileData.gender,
        orientation: profileData.orientation,
        goal: profileData.goal,
        bio: profileData.bio,
        city: profileData.city,
        latitude: profileData.latitude,
        longitude: profileData.longitude,
        geohash: profileData.geohash,
        photo_count: profileData.photos.length
      };
      
      const payload = {
        action: 'create_profile',
        profile: profileMetadata
      };
      
      console.log('Sending profile metadata to bot:', payload);
      
      // Store full profile data (including photos) in localStorage
      localStorage.setItem('profile_created', 'true');
      localStorage.setItem('profile_data', JSON.stringify(profileData));
      // Store user ID to validate profile ownership
      if (tg?.initDataUnsafe?.user?.id) {
        localStorage.setItem('profile_user_id', String(tg.initDataUnsafe.user.id));
      }
      
      // Haptic feedback on successful submission
      triggerHaptic('notification', 'success');
      
      // Send to bot (this will close the WebApp)
      tg.sendData(JSON.stringify(payload));
    } else {
      // Fallback: store only in localStorage (for testing without bot)
      localStorage.setItem('profile_created', 'true');
      localStorage.setItem('profile_data', JSON.stringify(profileData));
      // Store user ID to validate profile ownership
      if (tg?.initDataUnsafe?.user?.id) {
        localStorage.setItem('profile_user_id', String(tg.initDataUnsafe.user.id));
      }
      console.warn('Telegram WebApp not available, saving to localStorage only');
      
      // Haptic feedback on successful save
      triggerHaptic('notification', 'success');
      
      // Show success screen for demo
      showSuccessScreen();
    }
  } catch (error) {
    console.error('Error creating profile:', error);
    showFormError('Ошибка при создании анкеты. Попробуйте еще раз.');
  }
}

/**
 * Calculate geohash for coordinates (privacy-preserving location)
 */
function calculateGeohash(latitude, longitude, precision = 5) {
  const base32 = '0123456789bcdefghjkmnpqrstuvwxyz';
  
  let lat_min = -90.0, lat_max = 90.0;
  let lon_min = -180.0, lon_max = 180.0;
  
  let geohash = [];
  let bits = 0;
  let bit_count = 0;
  let even_bit = true;
  
  while (geohash.length < precision) {
    if (even_bit) {
      // Longitude
      const mid = (lon_min + lon_max) / 2;
      if (longitude > mid) {
        bits |= (1 << (4 - bit_count));
        lon_min = mid;
      } else {
        lon_max = mid;
      }
    } else {
      // Latitude
      const mid = (lat_min + lat_max) / 2;
      if (latitude > mid) {
        bits |= (1 << (4 - bit_count));
        lat_min = mid;
      } else {
        lat_max = mid;
      }
    }
    
    even_bit = !even_bit;
    bit_count++;
    
    if (bit_count === 5) {
      geohash.push(base32[bits]);
      bits = 0;
      bit_count = 0;
    }
  }
  
  return geohash.join('');
}

/**
 * Show form error
 */
function showFormError(message) {
  const errorEl = document.getElementById('formError');
  if (errorEl) {
    errorEl.textContent = message;
    errorEl.classList.remove('hidden');
    triggerHaptic('notification', 'error');
    
    // Auto-hide after 5 seconds
    setTimeout(() => {
      errorEl.classList.add('hidden');
    }, 5000);
  }
}

// ============================================================================
// Initialization
// ============================================================================

/**
 * Check and clear localStorage if app version changed
 */
function checkAndClearOldCache() {
  const storedVersion = localStorage.getItem('app_version');
  if (storedVersion !== APP_VERSION) {
    console.log(`App version changed from ${storedVersion} to ${APP_VERSION}, clearing cache`);
    localStorage.clear();
    localStorage.setItem('app_version', APP_VERSION);
  }
}

/**
 * Initialize the app
 */
async function init() {
  console.log('App initialization started');
  
  // Clear old cache if version changed
  checkAndClearOldCache();
  
  showLoading();
  
  // Wait for Telegram WebApp SDK to load
  await new Promise(resolve => {
    if (window.Telegram && window.Telegram.WebApp) {
      resolve();
    } else {
      window.addEventListener('load', resolve);
    }
  });
  
  // Initialize Telegram WebApp
  if (!initTelegramWebApp()) {
    return;
  }
  
  // Apply theme
  applyTheme();
  
  // Setup theme listener
  setupThemeListener();
  
  // Setup photo upload
  setupPhotoUpload();
  
  // Setup profile form
  setupProfileForm();
  
  // Check if user has profile
  const hasProfile = await checkUserProfile();
  
  if (hasProfile) {
    // Show success screen for existing users
    showSuccessScreen();
  } else {
    // Show onboarding for new users (Step 1: Welcome)
    showOnboarding();
  }
  
  // Ready notification
  tg.ready();
  
  console.log('App initialization complete');
}

// Start the app when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}
