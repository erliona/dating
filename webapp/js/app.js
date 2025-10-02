/**
 * Dating Mini App - Telegram WebApp Integration
 * Epic A1: Mini App initialization and bridge to Telegram WebApp API
 */

// ============================================================================
// Telegram WebApp Integration
// ============================================================================

let tg = null;
let initData = null;

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
  
  // Display platform info
  displayPlatformInfo();
  
  // Handle deep links
  const startParam = parseStartParam();
  if (startParam) {
    handleDeepLink(startParam);
  } else {
    showContent();
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
