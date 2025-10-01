(function () {
  // Debug logging utility
  const DEBUG_KEY = "dating-debug-mode";
  let debugMode = localStorage.getItem(DEBUG_KEY) === "true";
  
  function debug(...args) {
    if (debugMode) {
      console.log("[DEBUG]", ...args);
    }
  }

  // Utility: Debounce function for performance optimization
  function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
      const later = () => {
        clearTimeout(timeout);
        func(...args);
      };
      clearTimeout(timeout);
      timeout = setTimeout(later, wait);
    };
  }

  debug("App initializing...");

  // Telegram WebApp API
  const tg = window.Telegram?.WebApp;
  if (tg) {
    tg.ready();
    tg.expand();
    debug("Telegram WebApp initialized", tg);
  } else {
    debug("Telegram WebApp not available");
  }

  // Storage keys
  const STORAGE_KEY = "dating-webapp-profile-draft";
  const PROFILE_KEY = "dating-webapp-profile-data";
  const ONBOARDING_KEY = "dating-onboarding-completed";
  const SETTINGS_KEY = "dating-settings";

  // Load settings
  let settings = {
    lang: "ru",
    showLocation: true,
    showAge: true,
    notifyMatches: true,
    notifyMessages: true,
    ageMin: null,
    ageMax: null,
    maxDistance: null,
    debugMode: debugMode
  };
  
  try {
    const savedSettings = localStorage.getItem(SETTINGS_KEY);
    if (savedSettings) {
      settings = { ...settings, ...JSON.parse(savedSettings) };
      debug("Settings loaded", settings);
    }
  } catch (e) {
    debug("Error loading settings", e);
  }

  // Apply debug mode from settings
  debugMode = settings.debugMode;

  // Page management
  const pages = {
    onboarding: document.getElementById("onboarding-page"),
    profile: document.getElementById("profile-page"),
    matches: document.getElementById("matches-page"),
    settings: document.getElementById("settings-page")
  };

  const navBar = document.getElementById("nav-bar");
  const navButtons = document.querySelectorAll(".nav-item");

  let currentPage = null;

  function showPage(pageName) {
    debug("Navigating to page:", pageName);
    
    // Hide all pages
    Object.values(pages).forEach(page => {
      if (page) page.classList.remove("active");
    });

    // Show target page
    if (pages[pageName]) {
      pages[pageName].classList.add("active");
      currentPage = pageName;
    }

    // Update nav bar active state
    navButtons.forEach(btn => {
      if (btn.dataset.page === pageName) {
        btn.classList.add("active");
      } else {
        btn.classList.remove("active");
      }
    });

    // Show/hide nav bar
    if (pageName === "onboarding") {
      navBar.style.display = "none";
    } else {
      navBar.style.display = "flex";
    }

    debug("Current page:", currentPage);
  }

  // Navigation event listeners
  navButtons.forEach(btn => {
    btn.addEventListener("click", () => {
      const page = btn.dataset.page;
      showPage(page);
      
      // Load page content
      if (page === "matches") {
        loadMatches();
      }
    });
  });

  // ========================================
  // ONBOARDING
  // ========================================
  let currentOnboardingStep = "intro";
  const onboardingSteps = {
    intro: document.getElementById("onboarding-intro"),
    basic: document.getElementById("onboarding-basic"),
    photo: document.getElementById("onboarding-photo"),
    about: document.getElementById("onboarding-about"),
    final: document.getElementById("onboarding-final")
  };

  function showOnboardingStep(stepName) {
    debug("Showing onboarding step:", stepName);
    
    // Hide all steps
    Object.values(onboardingSteps).forEach(step => {
      if (step) step.style.display = "none";
    });
    
    // Show target step
    if (onboardingSteps[stepName]) {
      onboardingSteps[stepName].style.display = "block";
      currentOnboardingStep = stepName;
    }
  }

  // Onboarding navigation
  const startOnboardingBtn = document.getElementById("start-onboarding");
  const continueToBasicBtn = document.getElementById("continue-to-basic");
  const continueToPhotoBtn = document.getElementById("continue-to-about");
  const skipPhotoBtn = document.getElementById("skip-photo");
  const continueToFinishBtn = document.getElementById("continue-to-finish");
  const finishOnboardingBtn = document.getElementById("finish-onboarding");
  
  if (startOnboardingBtn) {
    startOnboardingBtn.addEventListener("click", () => {
      showOnboardingStep("basic");
    });
  }

  if (continueToBasicBtn) {
    continueToBasicBtn.addEventListener("click", () => {
      showOnboardingStep("photo");
    });
  }

  if (continueToPhotoBtn) {
    continueToPhotoBtn.addEventListener("click", () => {
      showOnboardingStep("about");
    });
  }

  if (skipPhotoBtn) {
    skipPhotoBtn.addEventListener("click", () => {
      showOnboardingStep("about");
    });
  }

  if (continueToFinishBtn) {
    continueToFinishBtn.addEventListener("click", () => {
      showOnboardingStep("final");
    });
  }

  if (finishOnboardingBtn) {
    finishOnboardingBtn.addEventListener("click", () => {
      debug("Onboarding completed");
      localStorage.setItem(ONBOARDING_KEY, "true");
      showPage("profile");
    });
  }

  // ========================================
  // PHOTO UPLOAD
  // ========================================
  let uploadedPhotoData = null;

  // Onboarding photo upload
  const photoFileInput = document.getElementById("photo-file-input");
  const uploadPhotoBtn = document.getElementById("upload-photo-btn");
  const photoPreview = document.getElementById("photo-preview");
  const photoUrlInput = document.getElementById("photo-url-input");

  if (uploadPhotoBtn && photoFileInput) {
    uploadPhotoBtn.addEventListener("click", () => {
      photoFileInput.click();
    });

    photoFileInput.addEventListener("change", (e) => {
      const file = e.target.files[0];
      if (file) {
        handlePhotoUpload(file, photoPreview, photoUrlInput);
      }
    });
  }

  // Profile form photo upload
  const profilePhotoFile = document.getElementById("profile-photo-file");
  const profilePhotoPreview = document.getElementById("profile-photo-preview");
  
  if (profilePhotoPreview && profilePhotoFile) {
    profilePhotoPreview.addEventListener("click", () => {
      profilePhotoFile.click();
    });

    profilePhotoFile.addEventListener("change", (e) => {
      const file = e.target.files[0];
      if (file) {
        const photoUrlField = form.elements["photo_url"];
        handlePhotoUpload(file, profilePhotoPreview, photoUrlField);
      }
    });
  }

  function handlePhotoUpload(file, previewElement, urlField) {
    debug("Photo selected:", file.name, file.size, file.type);
    
    // Validate file
    if (!file.type.startsWith('image/')) {
      showStatus("Пожалуйста, выбери изображение (JPG, PNG, GIF).", true);
      return;
    }
    
    if (file.size > 5 * 1024 * 1024) {
      showStatus("Файл слишком большой. Максимальный размер: 5 МБ.", true);
      return;
    }

    // Read file and create preview
    const reader = new FileReader();
    reader.onload = (e) => {
      const dataUrl = e.target.result;
      uploadedPhotoData = dataUrl;
      
      // Update preview
      if (previewElement) {
        previewElement.innerHTML = `<img src="${dataUrl}" alt="Preview" style="max-width: 100%; height: auto; border-radius: 8px;" />`;
      }
      
      // Store base64 in URL field (for Telegram WebApp data transfer)
      if (urlField) {
        urlField.value = dataUrl;
      }
      
      debug("Photo uploaded and encoded");
      showStatus("Фото загружено успешно!");
    };
    
    reader.onerror = () => {
      showStatus("Ошибка при загрузке фото. Попробуй еще раз.", true);
    };
    
    reader.readAsDataURL(file);
  }

  // ========================================
  // PROFILE FORM (existing logic)
  // ========================================
  const form = document.getElementById("profile-form");
  const status = document.getElementById("status");
  const autosaveStatus = document.getElementById("autosave-status");
  const progressFill = document.getElementById("progress-fill");
  const progressLabel = document.getElementById("progress-label");
  const progressContainer = document.getElementById("progress-container");
  const deleteBtn = document.getElementById("delete-btn");
  const submitBtn = document.getElementById("submit-btn");
  const pageTitle = document.getElementById("page-title");
  const pageHint = document.getElementById("page-hint");
  const saveDelay = 600;

  const fields = Array.from(form.elements).filter((element) =>
    Boolean(element.name)
  );
  const requiredFields = fields.filter((field) => field.required);

  const validationMessages = {
    name: {
      valueMissing: "Укажи имя, чтобы знакомство было личным.",
      patternMismatch: "Имя может содержать только буквы, пробелы и дефисы.",
      tooShort: "Имя должно содержать минимум 2 символа.",
      tooLong: "Имя должно быть короче 40 символов.",
    },
    age: {
      valueMissing: "Возраст помогает показывать анкеты подходящим людям.",
      rangeUnderflow: "Минимальный возраст — 18 лет.",
      rangeOverflow: "Укажи реалистичный возраст до 120 лет.",
      typeMismatch: "Используй только цифры для указания возраста.",
    },
    gender: {
      valueMissing: "Выбери пол, чтобы анкета была понятнее.",
    },
    preference: {
      valueMissing: "Подскажи, кого ищешь, чтобы показать тебя подходящим людям.",
    },
    bio: {
      tooLong: "Описание ограничено 400 символами.",
    },
    location: {
      tooLong: "Название города ограничено 60 символами.",
    },
    interests: {
      tooLong: "Поле интересов ограничено 120 символами.",
    },
    photo_url: {
      typeMismatch: "Введи корректный URL, начинающийся с https://.",
    },
  };

  function showStatus(message, isError = false) {
    debug("Status:", message, "isError:", isError);
    if (status) {
      status.textContent = message;
      status.style.color = isError
        ? "var(--tg-theme-destructive-text-color, #ef4444)"
        : "var(--tg-theme-link-color, #2563eb)";
    }
  }

  function getErrorMessage(field) {
    const validity = field.validity;
    const fieldMessages = validationMessages[field.name] || {};

    if (validity.valueMissing) return fieldMessages.valueMissing || "Обязательное поле.";
    if (validity.patternMismatch) return fieldMessages.patternMismatch || "Неверный формат.";
    if (validity.tooShort) return fieldMessages.tooShort || "Слишком короткое значение.";
    if (validity.tooLong) return fieldMessages.tooLong || "Слишком длинное значение.";
    if (validity.rangeUnderflow) return fieldMessages.rangeUnderflow || "Значение слишком мало.";
    if (validity.rangeOverflow) return fieldMessages.rangeOverflow || "Значение слишком велико.";
    if (validity.typeMismatch) return fieldMessages.typeMismatch || "Неверный тип данных.";

    return "";
  }

  function showFieldError(field, message) {
    const label = field.closest("label");
    if (!label) return;

    const errorSpan = label.querySelector(".error-message");
    if (errorSpan) {
      errorSpan.textContent = message || "";
    }

    if (message) {
      label.classList.add("invalid");
    } else {
      label.classList.remove("invalid");
    }
  }

  function handleFieldChange(field) {
    const message = getErrorMessage(field);
    showFieldError(field, message);
    updateProgress();
    scheduleSave();
  }

  function handleFieldBlur(field) {
    if (field.value.trim() || field.required) {
      const message = getErrorMessage(field);
      showFieldError(field, message);
    }
  }

  // Use debounced version for input events to improve performance
  const debouncedHandleFieldChange = debounce(handleFieldChange, 300);

  fields.forEach((field) => {
    field.addEventListener("input", () => debouncedHandleFieldChange(field));
    field.addEventListener("change", () => handleFieldChange(field));
    field.addEventListener("blur", () => handleFieldBlur(field));
  });

  function isFilled(field) {
    if (field.type === "checkbox" || field.type === "radio") {
      return field.checked;
    }
    return Boolean(field.value?.trim());
  }

  function updateProgress() {
    const totalRequired = requiredFields.length;
    const filledRequired = requiredFields.filter(isFilled).length;
    const percentage = Math.round((filledRequired / totalRequired) * 100);

    if (progressFill) {
      progressFill.style.width = `${percentage}%`;
    }
    if (progressLabel) {
      progressLabel.textContent = `Заполнено ${percentage}%`;
    }
    if (progressContainer && progressContainer.querySelector(".progress-track")) {
      progressContainer.querySelector(".progress-track").setAttribute("aria-valuenow", percentage);
    }

    debug("Progress updated:", percentage + "%");
  }

  let saveTimeout;

  function scheduleSave() {
    clearTimeout(saveTimeout);
    saveTimeout = setTimeout(saveDraft, saveDelay);
  }

  function saveDraft() {
    if (typeof localStorage === "undefined") return;

    const formData = new FormData(form);
    const draft = Object.fromEntries(formData.entries());

    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(draft));
      if (autosaveStatus) {
        autosaveStatus.textContent = "Черновик сохранён";
        setTimeout(() => {
          if (autosaveStatus) autosaveStatus.textContent = "";
        }, 2000);
      }
      debug("Draft saved", draft);
    } catch (e) {
      debug("Error saving draft", e);
    }
  }

  function restoreDraft() {
    if (typeof localStorage === "undefined") return;

    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        const draft = JSON.parse(stored);
        debug("Restoring draft", draft);

        fields.forEach((field) => {
          const value = draft[field.name];
          if (value !== undefined && value !== null) {
            if (field.type === "checkbox" || field.type === "radio") {
              field.checked = Boolean(value);
            } else {
              field.value = value;
            }
          }
        });

        updateProgress();
      }
    } catch (e) {
      debug("Error restoring draft", e);
    }
  }

  function checkExistingProfile() {
    if (typeof localStorage === "undefined") return false;

    try {
      const stored = localStorage.getItem(PROFILE_KEY);
      if (stored) {
        const profile = JSON.parse(stored);
        debug("Existing profile found", profile);
        loadProfile(profile);
        return true;
      }
    } catch (e) {
      debug("Error checking profile", e);
    }
    return false;
  }

  function loadProfile(profile) {
    debug("Loading profile into form", profile);
    
    // Update UI for editing mode
    if (pageTitle) {
      pageTitle.textContent = "Мой профиль";
    }
    if (pageHint) {
      pageHint.textContent = "Здесь ты можешь изменить информацию своего профиля или удалить его.";
    }
    if (submitBtn) {
      submitBtn.textContent = "Сохранить изменения";
    }
    if (deleteBtn) {
      deleteBtn.style.display = "block";
    }
    
    // Hide progress bar for editing
    if (progressContainer) {
      progressContainer.style.display = "none";
    }

    // Populate form fields
    fields.forEach((field) => {
      const value = profile[field.name];
      if (value !== undefined && value !== null) {
        if (field.type === "checkbox" || field.type === "radio") {
          field.checked = Boolean(value);
        } else if (field.name === "interests" && Array.isArray(value)) {
          field.value = value.join(", ");
        } else {
          field.value = value;
        }
      }
    });
    
    updateProgress();
  }

  // Check for existing profile on load
  const hasProfile = checkExistingProfile();
  if (!hasProfile) {
    restoreDraft();
  }

  // Delete button handler
  if (deleteBtn) {
    deleteBtn.addEventListener("click", () => {
      debug("Delete button clicked");
      
      if (!confirm("Вы действительно хотите удалить свой профиль? Это действие нельзя отменить.")) {
        return;
      }

      if (!tg) {
        showStatus("Невозможно удалить профиль без Telegram.", true);
        return;
      }

      const payload = { action: "delete" };
      debug("Sending delete request", payload);
      tg.sendData(JSON.stringify(payload));
      
      // Clear local storage
      if (typeof localStorage !== "undefined") {
        localStorage.removeItem(PROFILE_KEY);
        localStorage.removeItem(STORAGE_KEY);
        debug("Local storage cleared");
      }
      
      // Don't close the app automatically - let user decide
      showStatus("Профиль успешно удалён. Ты можешь создать новый профиль или закрыть приложение.");
    });
  }

  // Form submit handler
  form.addEventListener("submit", (event) => {
    event.preventDefault();
    debug("Form submitted");
    
    let hasErrors = false;

    fields.forEach((field) => {
      const message = getErrorMessage(field);
      showFieldError(field, message);
      if (message) {
        hasErrors = true;
      }
    });

    if (hasErrors) {
      showStatus("Проверь заполнение полей и исправь подсвеченные ошибки.", true);
      return;
    }

    const formData = new FormData(form);
    const payload = Object.fromEntries(formData.entries());

    const trim = (value) => (typeof value === "string" ? value.trim() : value);

    payload.name = trim(payload.name);
    payload.age = trim(payload.age);
    payload.bio = trim(payload.bio);

    const location = trim(payload.location);
    if (location) {
      payload.location = location;
    } else {
      delete payload.location;
    }

    const interestsRaw = trim(payload.interests);
    if (interestsRaw) {
      payload.interests = interestsRaw
        .split(",")
        .map((item) => item.trim())
        .filter(Boolean);
    } else {
      payload.interests = [];
    }

    if (!payload.goal) {
      delete payload.goal;
    }

    const photoUrl = trim(payload.photo_url);
    if (photoUrl) {
      try {
        const url = new URL(photoUrl);
        if (url.protocol !== 'https:') {
          showStatus("Ссылка на фото должна использовать HTTPS для безопасности.", true);
          return;
        }
        payload.photo_url = photoUrl;
      } catch (error) {
        showStatus("Указан некорректный URL для фото.", true);
        return;
      }
    } else {
      delete payload.photo_url;
    }

    if (!payload.bio) {
      delete payload.bio;
    }

    if (!tg) {
      showStatus("Невозможно отправить данные без Telegram.", true);
      return;
    }

    debug("Sending profile data", payload);
    tg.sendData(JSON.stringify(payload));
    
    // Save profile data for future editing
    if (typeof localStorage !== "undefined") {
      localStorage.setItem(PROFILE_KEY, JSON.stringify(payload));
      localStorage.removeItem(STORAGE_KEY);
      debug("Profile saved to localStorage");
    }
    
    // Don't close the app automatically - let user decide
    showStatus("Анкета успешно отправлена! Теперь можешь перейти к просмотру метчей.");

    if (autosaveStatus) {
      autosaveStatus.textContent = "";
    }
  });

  // ========================================
  // MATCHES PAGE
  // ========================================
  const matchesContainer = document.getElementById("matches-container");

  // Loading state management
  const LoadingState = {
    IDLE: 'idle',
    LOADING: 'loading',
    SUCCESS: 'success',
    ERROR: 'error'
  };

  let currentLoadingState = LoadingState.IDLE;

  function setLoadingState(state) {
    currentLoadingState = state;
    debug("Loading state changed to:", state);
  }

  function renderLoadingState() {
    if (!matchesContainer) return;

    const loadingHTML = '<div class="loading">Загрузка...</div>';
    matchesContainer.innerHTML = loadingHTML;
  }

  function renderEmptyState() {
    if (!matchesContainer) return;

    const emptyHTML = `
      <div class="empty-state">
        <div class="empty-state-icon">😊</div>
        <p>Пока нет подходящих анкет</p>
        <p style="font-size: 0.9rem;">Проверь позже или измени настройки поиска</p>
      </div>
    `;
    matchesContainer.innerHTML = emptyHTML;
  }

  function renderErrorState(message = "Произошла ошибка при загрузке") {
    if (!matchesContainer) return;

    const errorHTML = `
      <div class="empty-state">
        <div class="empty-state-icon">😕</div>
        <p>${message}</p>
        <button class="primary" onclick="window.retryLoadMatches()">Попробовать снова</button>
      </div>
    `;
    matchesContainer.innerHTML = errorHTML;
  }

  // Test profiles for demo
  const testProfiles = [
    {
      id: 1,
      name: "Анна",
      age: 25,
      location: "Москва",
      bio: "Люблю путешествия, фотографию и хорошую музыку. Ищу единомышленников для общения и новых приключений.",
      interests: ["Путешествия", "Фотография", "Музыка"],
      photo_url: null
    },
    {
      id: 2,
      name: "Дмитрий",
      age: 28,
      location: "Санкт-Петербург",
      bio: "IT-специалист, увлекаюсь спортом и кулинарией. Хочу найти интересного собеседника.",
      interests: ["IT", "Спорт", "Кулинария"],
      photo_url: null
    },
    {
      id: 3,
      name: "Елена",
      age: 23,
      location: "Казань",
      bio: "Художник и любитель книг. Ищу творческих людей для дружбы и общения.",
      interests: ["Искусство", "Книги", "Кино"],
      photo_url: null
    }
  ];

  // Create profile card HTML
  function createProfileCard(profile) {
    const photoHTML = profile.photo_url 
      ? `<img src="${profile.photo_url}" alt="${profile.name}">`
      : profile.name.charAt(0);
    
    const bioHTML = profile.bio 
      ? `<p class="match-bio">${profile.bio}</p>` 
      : "";
    
    const interestsHTML = profile.interests && profile.interests.length > 0
      ? `<div class="match-interests">
           ${profile.interests.map(interest => `<span class="interest-tag">${interest}</span>`).join("")}
         </div>`
      : "";

    return `
      <div class="match-card" data-profile-id="${profile.id}">
        <div class="match-header">
          <div class="match-photo">${photoHTML}</div>
          <div class="match-info">
            <h3 class="match-name">${profile.name}, ${profile.age}</h3>
            <p class="match-meta">${profile.location || "Местоположение не указано"}</p>
          </div>
        </div>
        ${bioHTML}
        ${interestsHTML}
        <div class="match-actions">
          <button class="secondary" data-action="dislike" data-profile-id="${profile.id}">Пропустить</button>
          <button class="primary" data-action="like" data-profile-id="${profile.id}">Лайк ❤️</button>
        </div>
      </div>
    `;
  }

  function renderMatches(profiles) {
    if (!matchesContainer) return;

    const fragment = document.createDocumentFragment();
    const tempDiv = document.createElement('div');
    tempDiv.innerHTML = profiles.map(createProfileCard).join("");
    
    while (tempDiv.firstChild) {
      fragment.appendChild(tempDiv.firstChild);
    }
    
    matchesContainer.innerHTML = "";
    matchesContainer.appendChild(fragment);
    
    debug("Matches rendered:", profiles.length);
  }

  function loadMatches() {
    debug("Loading matches");
    
    if (!matchesContainer) return;

    setLoadingState(LoadingState.LOADING);
    renderLoadingState();

    // Simulate loading delay
    setTimeout(() => {
      try {
        // Filter test profiles based on user preferences
        let filteredProfiles = [...testProfiles];
        
        // Apply age filters if set
        if (settings.ageMin) {
          filteredProfiles = filteredProfiles.filter(p => p.age >= settings.ageMin);
        }
        if (settings.ageMax) {
          filteredProfiles = filteredProfiles.filter(p => p.age <= settings.ageMax);
        }
        
        debug("Filtered profiles:", filteredProfiles.length, "of", testProfiles.length);
        
        if (filteredProfiles.length === 0) {
          setLoadingState(LoadingState.SUCCESS);
          renderEmptyState();
          return;
        }

        setLoadingState(LoadingState.SUCCESS);
        renderMatches(filteredProfiles);
      } catch (error) {
        debug("Error loading matches:", error);
        setLoadingState(LoadingState.ERROR);
        renderErrorState();
      }
    }, 500);
  }

  // Retry function for error state
  window.retryLoadMatches = loadMatches;

  function sendInteraction(targetUserId, action) {
    debug(`Sending ${action} to user ${targetUserId}`);
    
    if (!tg) {
      showStatus(`Невозможно отправить действие без Telegram.`, true);
      return;
    }

    const payload = {
      action: action,
      target_user_id: targetUserId
    };

    debug("Sending interaction data", payload);
    tg.sendData(JSON.stringify(payload));
  }

  function handleLike(profileId) {
    debug("Like profile:", profileId);
    sendInteraction(profileId, "like");
    removeProfileFromView(profileId);
  }

  function handleDislike(profileId) {
    debug("Dislike profile:", profileId);
    sendInteraction(profileId, "dislike");
    removeProfileFromView(profileId);
  }

  function removeProfileFromView(profileId) {
    // Remove the profile from the test data
    const index = testProfiles.findIndex(p => p.id === profileId);
    if (index > -1) {
      testProfiles.splice(index, 1);
    }
    // Reload the matches view
    loadMatches();
  }

  // Event delegation for match actions (better performance)
  if (matchesContainer) {
    matchesContainer.addEventListener("click", (event) => {
      const button = event.target.closest("button[data-action]");
      if (!button) return;

      const action = button.dataset.action;
      const profileId = parseInt(button.dataset.profileId, 10);

      if (!profileId) return;

      if (action === "like") {
        handleLike(profileId);
      } else if (action === "dislike") {
        handleDislike(profileId);
      }
    });
  }

  // Keep global functions for backward compatibility
  window.handleLike = handleLike;
  window.handleDislike = handleDislike;

  // ========================================
  // SETTINGS PAGE
  // ========================================
  const langSelect = document.getElementById("lang-select");
  const showLocationToggle = document.getElementById("show-location");
  const showAgeToggle = document.getElementById("show-age");
  const notifyMatchesToggle = document.getElementById("notify-matches");
  const notifyMessagesToggle = document.getElementById("notify-messages");
  const ageMinInput = document.getElementById("age-min");
  const ageMaxInput = document.getElementById("age-max");
  const maxDistanceInput = document.getElementById("max-distance");
  const debugModeToggle = document.getElementById("debug-mode");
  const logoutBtn = document.getElementById("logout-btn");
  const clearDataBtn = document.getElementById("clear-data-btn");

  // Load settings into UI
  function loadSettings() {
    debug("Loading settings into UI");
    
    if (langSelect) langSelect.value = settings.lang;
    if (showLocationToggle) showLocationToggle.checked = settings.showLocation;
    if (showAgeToggle) showAgeToggle.checked = settings.showAge;
    if (notifyMatchesToggle) notifyMatchesToggle.checked = settings.notifyMatches;
    if (notifyMessagesToggle) notifyMessagesToggle.checked = settings.notifyMessages;
    if (ageMinInput) ageMinInput.value = settings.ageMin || "";
    if (ageMaxInput) ageMaxInput.value = settings.ageMax || "";
    if (maxDistanceInput) maxDistanceInput.value = settings.maxDistance || "";
    if (debugModeToggle) debugModeToggle.checked = settings.debugMode;
  }

  // Save settings
  function saveSettings() {
    const ageMin = ageMinInput?.value ? parseInt(ageMinInput.value, 10) : null;
    const ageMax = ageMaxInput?.value ? parseInt(ageMaxInput.value, 10) : null;
    const maxDistance = maxDistanceInput?.value ? parseInt(maxDistanceInput.value, 10) : null;
    
    settings = {
      lang: langSelect?.value || "ru",
      showLocation: showLocationToggle?.checked ?? true,
      showAge: showAgeToggle?.checked ?? true,
      notifyMatches: notifyMatchesToggle?.checked ?? true,
      notifyMessages: notifyMessagesToggle?.checked ?? true,
      ageMin: ageMin,
      ageMax: ageMax,
      maxDistance: maxDistance,
      debugMode: debugModeToggle?.checked ?? false
    };

    if (typeof localStorage !== "undefined") {
      localStorage.setItem(SETTINGS_KEY, JSON.stringify(settings));
      localStorage.setItem(DEBUG_KEY, settings.debugMode.toString());
      debug("Settings saved to localStorage", settings);
    }

    // Update debug mode
    debugMode = settings.debugMode;
    
    // Send settings to bot for persistence in database
    if (tg) {
      const payload = {
        action: "update_settings",
        lang: settings.lang,
        show_location: settings.showLocation,
        show_age: settings.showAge,
        notify_matches: settings.notifyMatches,
        notify_messages: settings.notifyMessages,
        age_min: settings.ageMin,
        age_max: settings.ageMax,
        max_distance: settings.maxDistance
      };
      debug("Sending settings to bot", payload);
      tg.sendData(JSON.stringify(payload));
    } else {
      debug("Telegram WebApp not available, settings saved locally only");
      alert("Настройки сохранены локально!");
    }
  }

  // Settings event listeners
  if (langSelect) {
    langSelect.addEventListener("change", saveSettings);
  }

  [showLocationToggle, showAgeToggle, notifyMatchesToggle, notifyMessagesToggle, debugModeToggle].forEach(toggle => {
    if (toggle) {
      toggle.addEventListener("change", saveSettings);
    }
  });

  if (logoutBtn) {
    logoutBtn.addEventListener("click", () => {
      debug("Logout clicked");
      
      if (!confirm("Вы действительно хотите выйти? Все несохранённые изменения будут потеряны.")) {
        return;
      }

      // Clear all data
      if (typeof localStorage !== "undefined") {
        localStorage.removeItem(PROFILE_KEY);
        localStorage.removeItem(STORAGE_KEY);
        debug("Logged out, data cleared");
      }

      alert("Вы вышли из аккаунта. Данные очищены.");
      
      // Return to onboarding
      localStorage.removeItem(ONBOARDING_KEY);
      showPage("onboarding");
    });
  }

  if (clearDataBtn) {
    clearDataBtn.addEventListener("click", () => {
      debug("Clear data clicked");
      
      if (!confirm("Вы уверены? Все локальные данные будут удалены.")) {
        return;
      }

      if (typeof localStorage !== "undefined") {
        localStorage.clear();
        debug("All localStorage cleared");
      }

      alert("Локальные данные очищены!");
    });
  }

  // ========================================
  // INITIALIZATION
  // ========================================
  loadSettings();

  // Check if onboarding is needed
  const onboardingCompleted = localStorage.getItem(ONBOARDING_KEY) === "true";
  
  if (!onboardingCompleted) {
    debug("Showing onboarding");
    showPage("onboarding");
  } else {
    debug("Onboarding completed, showing profile");
    showPage("profile");
  }

  debug("App initialized successfully");
})();
