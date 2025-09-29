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

    if (!tg) {
      showStatus("Невозможно отправить данные без Telegram.", true);
      return;
    }

    tg.sendData(JSON.stringify(payload));
    tg.close();
    showStatus("Анкета отправлена, спасибо!");
  });
})();
