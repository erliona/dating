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
  // Check if user has completed profile creation
  return localStorage.getItem('profile_created') === 'true';
}

/**
 * Show onboarding screen (Welcome)
 */
function showOnboarding() {
  document.getElementById('loading').classList.add('hidden');
  document.getElementById('onboarding').classList.remove('hidden');
  document.getElementById('profile-form').classList.add('hidden');
  document.getElementById('success-screen').classList.add('hidden');
  
  // Haptic feedback
  triggerHaptic('impact', 'light');
}

/**
 * Start profile creation (Step 2: Registration Form)
 */
function startProfileCreation() {
  document.getElementById('onboarding').classList.add('hidden');
  document.getElementById('profile-form').classList.remove('hidden');
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
  triggerHaptic('notification', 'success');
}

// ============================================================================
// Geolocation Detection
// ============================================================================

/**
 * Detect user location using Telegram WebApp API and browser geolocation
 */
async function detectUserLocation() {
  const statusEl = document.getElementById('locationStatus');
  const detectBtn = document.getElementById('detectLocationBtn');
  const cityInput = document.getElementById('cityInput');
  const latInput = document.getElementById('latitude');
  const lonInput = document.getElementById('longitude');
  
  if (!statusEl || !detectBtn) return;
  
  // Show detecting status
  statusEl.className = 'location-status detecting';
  statusEl.textContent = '🔍 Определяем ваше местоположение...';
  statusEl.classList.remove('hidden');
  detectBtn.disabled = true;
  
  try {
    // First try Telegram's location API
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
    
    // Fallback to browser geolocation API
    if ('geolocation' in navigator) {
      navigator.geolocation.getCurrentPosition(
        async (position) => {
          await handleLocationSuccess(
            position.coords.latitude,
            position.coords.longitude
          );
        },
        (error) => {
          handleLocationError(error);
        },
        {
          enableHighAccuracy: true,
          timeout: 10000,
          maximumAge: 0
        }
      );
    } else {
      handleLocationError(new Error('Geolocation not supported'));
    }
  } catch (error) {
    handleLocationError(error);
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
  const uploadZone = document.getElementById('photoUploadZone');
  const photoInput = document.getElementById('photoInput');
  
  if (!uploadZone || !photoInput) return;
  
  uploadZone.addEventListener('click', () => {
    if (uploadedPhotos.length < 3) {
      photoInput.click();
    }
  });
  
  photoInput.addEventListener('change', (e) => {
    const files = Array.from(e.target.files);
    handlePhotoUpload(files);
    // Reset input to allow selecting same file again
    photoInput.value = '';
  });
  
  // Drag and drop
  uploadZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    if (uploadedPhotos.length < 3) {
      uploadZone.style.borderColor = 'var(--tg-theme-button-color)';
    }
  });
  
  uploadZone.addEventListener('dragleave', (e) => {
    e.preventDefault();
    uploadZone.style.borderColor = 'var(--tg-theme-hint-color)';
  });
  
  uploadZone.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadZone.style.borderColor = 'var(--tg-theme-hint-color)';
    
    if (uploadedPhotos.length < 3) {
      const files = Array.from(e.dataTransfer.files).filter(f => f.type.startsWith('image/'));
      handlePhotoUpload(files);
    }
  });
}

/**
 * Handle photo upload
 */
function handlePhotoUpload(files) {
  files.forEach(file => {
    // Check if we already have 3 photos
    if (uploadedPhotos.length >= 3) {
      showFormError('Максимум 3 фотографии');
      return;
    }
    
    // Validate file
    if (!file.type.startsWith('image/')) {
      showFormError('Пожалуйста, выберите изображение');
      return;
    }
    
    if (file.size > 5 * 1024 * 1024) {
      showFormError('Файл слишком большой. Максимум 5 МБ');
      return;
    }
    
    // Read and add photo
    const reader = new FileReader();
    reader.onload = (e) => {
      uploadedPhotos.push(e.target.result);
      updatePhotoPreview();
      triggerHaptic('notification', 'success');
    };
    
    reader.readAsDataURL(file);
  });
}

/**
 * Update photo preview display
 */
function updatePhotoPreview() {
  const container = document.getElementById('photoPreviewContainer');
  const counter = document.getElementById('photoCount');
  
  if (!container || !counter) return;
  
  // Update counter
  counter.textContent = uploadedPhotos.length;
  
  // Clear container
  container.innerHTML = '';
  
  // Add photo previews
  uploadedPhotos.forEach((photo, index) => {
    const item = document.createElement('div');
    item.className = 'photo-preview-item';
    
    const img = document.createElement('img');
    img.src = photo;
    img.alt = `Photo ${index + 1}`;
    
    const removeBtn = document.createElement('button');
    removeBtn.className = 'remove-photo';
    removeBtn.textContent = '×';
    removeBtn.onclick = () => removePhoto(index);
    
    item.appendChild(img);
    item.appendChild(removeBtn);
    container.appendChild(item);
  });
}

/**
 * Remove photo from upload list
 */
function removePhoto(index) {
  uploadedPhotos.splice(index, 1);
  updatePhotoPreview();
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
  // Validate photos (must have exactly 3)
  if (uploadedPhotos.length !== 3) {
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
  
  // Add photos
  profileData.photos = uploadedPhotos;
  
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
    // In production, this would send data to backend
    // Backend will store exact coordinates for matching nearest users
    // For now, store in localStorage
    localStorage.setItem('profile_created', 'true');
    localStorage.setItem('profile_data', JSON.stringify(profileData));
    
    console.log('Profile created:', profileData);
    
    // Show success screen
    showSuccessScreen();
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
 * Initialize the app
 */
async function init() {
  console.log('App initialization started');
  
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
