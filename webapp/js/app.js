(function () {
  const tg = window.Telegram?.WebApp;
  const form = document.getElementById("profile-form");
  const status = document.getElementById("status");

  if (tg) {
    tg.ready();
    tg.expand();
  }

  function showStatus(message, isError = false) {
    status.textContent = message;
    status.style.color = isError
      ? "var(--tg-theme-destructive-text-color, #ef4444)"
      : "var(--tg-theme-link-color, #2563eb)";
  }

  form.addEventListener("submit", (event) => {
    event.preventDefault();
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
      payload.photo_url = photoUrl;
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
    tg.close();
    showStatus("Анкета отправлена, спасибо!");
  });
})();
