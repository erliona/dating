(function () {
  const tg = window.Telegram?.WebApp;
  const form = document.getElementById("profile-form");
  const status = document.getElementById("status");
  const autosaveStatus = document.getElementById("autosave-status");
  const progressTrack = document.querySelector(".progress-track");
  const progressFill = document.getElementById("progress-fill");
  const progressLabel = document.getElementById("progress-label");
  const deleteBtn = document.getElementById("delete-btn");
  const submitBtn = document.getElementById("submit-btn");
  const pageTitle = document.getElementById("page-title");
  const pageHint = document.getElementById("page-hint");
  const progressContainer = document.getElementById("progress-container");
  const STORAGE_KEY = "dating-webapp-profile-draft";
  const PROFILE_KEY = "dating-webapp-profile-data";
  const saveDelay = 600;

  if (tg) {
    tg.ready();
    tg.expand();
  }

  const fields = Array.from(form.elements).filter((element) =>
    Boolean(element.name)
  );
  const requiredFields = fields.filter((field) => field.required);
  const optionalFields = fields.filter((field) => !field.required);

  const validationMessages = {
    name: {
      valueMissing: "Укажи имя, чтобы знакомство было личным.",
      patternMismatch:
        "Имя может содержать только буквы, пробелы и дефисы.",
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
      tooLong: "Название города слишком длинное — сократи его до 60 символов.",
    },
    interests: {
      tooLong: "Интересы ограничены 120 символами.",
    },
    goal: {
      tooLong: "Сократи цель знакомства до разумного описания.",
    },
    photo_url: {
      typeMismatch: "Похоже, ссылка указана неверно. Проверь формат URL.",
      tooLong: "Сократи ссылку на фото, если она слишком длинная.",
    },
  };

  function showStatus(message, isError = false) {
    status.textContent = message;
    status.style.color = isError
      ? "var(--tg-theme-destructive-text-color, #ef4444)"
      : "var(--tg-theme-link-color, #2563eb)";
  }

  function getErrorMessage(field) {
    if (field.validity.valid) {
      return "";
    }

    const messages = validationMessages[field.name] ?? {};
    const validity = field.validity;

    return (
      (validity.valueMissing && messages.valueMissing) ||
      (validity.patternMismatch && messages.patternMismatch) ||
      (validity.rangeUnderflow && messages.rangeUnderflow) ||
      (validity.rangeOverflow && messages.rangeOverflow) ||
      (validity.typeMismatch && messages.typeMismatch) ||
      (validity.tooShort && messages.tooShort) ||
      (validity.tooLong && messages.tooLong) ||
      (validity.stepMismatch && messages.stepMismatch) ||
      field.validationMessage
    );
  }

  function showFieldError(field, message) {
    const container = field.closest("label");
    const errorElement = container?.querySelector(".error-message");
    if (!errorElement) {
      return;
    }

    if (message) {
      container.classList.add("invalid");
      errorElement.textContent = message;
    } else {
      container.classList.remove("invalid");
      errorElement.textContent = "";
    }
  }

  function handleFieldChange(field) {
    field.dataset.dirty = "true";
    const message = getErrorMessage(field);
    showFieldError(field, message);
    scheduleSave();
    updateProgress();
  }

  function handleFieldBlur(field) {
    const message = getErrorMessage(field);
    showFieldError(field, message);
  }

  fields.forEach((field) => {
    field.addEventListener("input", () => handleFieldChange(field));
    field.addEventListener("change", () => handleFieldChange(field));
    field.addEventListener("blur", () => handleFieldBlur(field));
  });

  function isFilled(field) {
    if (field.type === "checkbox" || field.type === "radio") {
      return field.checked;
    }
    const value = field.value.trim();
    if (field.type === "select-one") {
      return value !== "";
    }
    return value.length > 0;
  }

  function updateProgress() {
    const requiredFilled = requiredFields.filter(isFilled).length;
    const optionalFilled = optionalFields.filter(isFilled).length;

    const requiredWeight = 70;
    const optionalWeight = 30;

    const requiredPercent =
      requiredFields.length > 0
        ? (requiredFilled / requiredFields.length) * requiredWeight
        : 0;
    const optionalPercent =
      optionalFields.length > 0
        ? (optionalFilled / optionalFields.length) * optionalWeight
        : 0;

    const progress = Math.round(requiredPercent + optionalPercent);

    if (progressFill) {
      progressFill.style.width = `${progress}%`;
    }
    if (progressTrack) {
      progressTrack.setAttribute("aria-valuenow", String(progress));
    }
    if (progressLabel) {
      progressLabel.textContent = `Заполнено ${progress}%`;
    }
  }

  let saveTimeout;

  function scheduleSave() {
    if (typeof localStorage === "undefined") {
      return;
    }
    clearTimeout(saveTimeout);
    saveTimeout = setTimeout(saveDraft, saveDelay);
  }

  function saveDraft() {
    if (typeof localStorage === "undefined") {
      return;
    }

    const snapshot = {};
    fields.forEach((field) => {
      if (field.type === "checkbox" || field.type === "radio") {
        snapshot[field.name] = field.checked;
      } else {
        snapshot[field.name] = field.value;
      }
    });

    localStorage.setItem(STORAGE_KEY, JSON.stringify(snapshot));
    if (autosaveStatus) {
      const time = new Date().toLocaleTimeString("ru-RU", {
        hour: "2-digit",
        minute: "2-digit",
      });
      autosaveStatus.textContent = `Черновик сохранён в ${time}`;
    }
  }

  function restoreDraft() {
    if (typeof localStorage === "undefined") {
      return;
    }

    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) {
      updateProgress();
      return;
    }

    try {
      const snapshot = JSON.parse(raw);
      fields.forEach((field) => {
        if (!(field.name in snapshot)) {
          return;
        }
        if (field.type === "checkbox" || field.type === "radio") {
          field.checked = Boolean(snapshot[field.name]);
        } else {
          field.value = snapshot[field.name];
        }
      });
      if (autosaveStatus) {
        autosaveStatus.textContent = "Черновик загружен — можно продолжить заполнение.";
      }
    } catch (error) {
      console.error("Не удалось восстановить черновик", error);
    }

    updateProgress();
  }

  function checkExistingProfile() {
    // Check if we have a saved profile (would be set when form is submitted)
    if (typeof localStorage === "undefined") {
      return false;
    }
    
    const profileData = localStorage.getItem(PROFILE_KEY);
    if (profileData) {
      try {
        const profile = JSON.parse(profileData);
        loadProfile(profile);
        return true;
      } catch (error) {
        console.error("Failed to load existing profile", error);
      }
    }
    return false;
  }

  function loadProfile(profile) {
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
  }

  // Check for existing profile on load
  const hasProfile = checkExistingProfile();
  if (!hasProfile) {
    restoreDraft();
  }

  // Delete button handler
  if (deleteBtn) {
    deleteBtn.addEventListener("click", () => {
      if (!confirm("Вы действительно хотите удалить свой профиль? Это действие нельзя отменить.")) {
        return;
      }

      if (!tg) {
        showStatus("Невозможно удалить профиль без Telegram.", true);
        return;
      }

      const payload = { action: "delete" };
      tg.sendData(JSON.stringify(payload));
      
      // Clear local storage
      if (typeof localStorage !== "undefined") {
        localStorage.removeItem(PROFILE_KEY);
        localStorage.removeItem(STORAGE_KEY);
      }
      
      tg.close();
      showStatus("Профиль удаляется...");
    });
  }

  form.addEventListener("submit", (event) => {
    event.preventDefault();
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

    tg.sendData(JSON.stringify(payload));
    
    // Save profile data for future editing
    if (typeof localStorage !== "undefined") {
      localStorage.setItem(PROFILE_KEY, JSON.stringify(payload));
      localStorage.removeItem(STORAGE_KEY);
    }
    
    tg.close();
    showStatus("Анкета отправлена, спасибо!");

    if (autosaveStatus) {
      autosaveStatus.textContent = "";
    }
  });
})();
