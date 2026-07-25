(() => {
  "use strict";

  const form = document.getElementById("contact-form");
  const status = document.getElementById("contact-status");
  const submitButton = form?.querySelector('button[type="submit"]');

  if (!form || !status || !submitButton) {
    return;
  }

  const contactApiUrl =
    "https://bhagyesh-contact-api.bhagyesh-chokhawala.workers.dev/contact";

  form.addEventListener("submit", async (event) => {
    event.preventDefault();

    if (!form.reportValidity()) {
      return;
    }

    const data = new FormData(form);
    const payload = {
      name: String(data.get("name") || "").trim(),
      organization: String(data.get("organization") || "").trim(),
      contact: String(data.get("contact") || "").trim(),
      topic: String(data.get("topic") || "").trim(),
      subject: String(data.get("subject") || "").trim(),
      message: String(data.get("message") || "").trim(),
      publicConfirmation: data.get("public_confirmation") === "on",
      website: String(data.get("website") || "").trim()
    };

    submitButton.disabled = true;
    submitButton.textContent = "Submitting…";
    status.textContent = "Submitting your contact request…";

    try {
      const response = await fetch(contactApiUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify(payload)
      });

      let result = {};

      try {
        result = await response.json();
      } catch {
        result = {};
      }

      if (!response.ok) {
        throw new Error(
          result.error ||
            "Unable to submit your contact request. Please try again."
        );
      }

      form.reset();
      status.textContent =
        result.message || "Your contact request was submitted successfully.";
    } catch (error) {
      status.textContent =
        error instanceof Error
          ? error.message
          : "Unable to submit your contact request. Please try again.";
    } finally {
      submitButton.disabled = false;
      submitButton.textContent = "Submit Contact";
    }
  });
})();
