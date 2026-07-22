(() => {
  "use strict";

  const form = document.getElementById("contact-form");
  const status = document.getElementById("contact-status");

  if (!form) {
    return;
  }

  const repositoryIssueUrl =
    "https://github.com/Bhagyesh-Chokhawala/" +
    "bhagyesh-chokhawala.github.io/issues/new";

  form.addEventListener("submit", (event) => {
    event.preventDefault();

    if (!form.reportValidity()) {
      return;
    }

    const data = new FormData(form);
    const subject = String(data.get("subject") || "").trim();

    const params = new URLSearchParams({
      template: "contact.yml",
      title: `[Contact]: ${subject}`,
      name: String(data.get("name") || "").trim(),
      organization: String(data.get("organization") || "").trim(),
      contact: String(data.get("contact") || "").trim(),
      topic: String(data.get("topic") || "").trim(),
      message: String(data.get("message") || "").trim()
    });

    const issueUrl = `${repositoryIssueUrl}?${params.toString()}`;
    const issueWindow = window.open(issueUrl, "_blank", "noopener,noreferrer");

    if (issueWindow) {
      status.textContent =
        "GitHub opened in a new tab. Review the request and submit the issue.";
    } else {
      status.textContent =
        "Your browser blocked the new tab. Please allow pop-ups and try again.";
    }
  });
})();
