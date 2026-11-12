(function () {
  "use strict";

  const form = document.getElementById("contactForm");
  if (!form) return;

  const submitBtn = document.getElementById("contactSubmitBtn");
  const btnText = document.getElementById("contactSubmitText");
  const btnSpinner = document.getElementById("contactSubmitSpinner");
  const statusRegion = document.getElementById("contactStatusRegion");
  const messageInput = document.getElementById("id_message");
  const charCountEl = document.getElementById("messageCharCount");
  const attachmentInput = document.getElementById("id_attachment");
  const filePreviewEl = document.getElementById("attachmentPreview");
  const fileNameEl = document.getElementById("attachmentFileName");
  const fileClearBtn = document.getElementById("clearAttachmentBtn");

  const maxBytes = Number(form.dataset.maxBytes || 5 * 1024 * 1024);
  const allowedExts = (form.dataset.allowedExts || ".pdf,.png,.jpg,.jpeg,.webp,.txt")
    .split(",")
    .map((s) => s.trim().toLowerCase())
    .filter(Boolean);

  const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;
  const touchedFields = new WeakSet();
  let isSubmitting = false;

  // Polite live region for screen reader announcements on blur/change.
  const announcer = document.createElement("div");
  announcer.setAttribute("aria-live", "polite");
  announcer.className = "visually-hidden";
  document.body.appendChild(announcer);

  function linkError(field, show) {
    const errorId = field.dataset.error;
    if (!errorId) return;
    const ids = (field.getAttribute("aria-describedby") || "")
      .split(/\s+/)
      .filter((id) => id && id !== errorId);
    if (show) ids.push(errorId);
    if (ids.length) {
      field.setAttribute("aria-describedby", ids.join(" "));
    } else {
      field.removeAttribute("aria-describedby");
    }
  }

  function setFieldError(field, message) {
    const errorEl = document.getElementById(field.dataset.error || "");
    if (message) {
      field.classList.add("is-invalid");
      field.setAttribute("aria-invalid", "true");
      linkError(field, true);
      if (errorEl) {
        const textSpan = errorEl.querySelector("[data-error-text]");
        if (textSpan) textSpan.textContent = message;
        errorEl.classList.add("is-visible");
      }
    } else {
      field.classList.remove("is-invalid");
      field.setAttribute("aria-invalid", "false");
      linkError(field, false);
      if (errorEl) {
        errorEl.classList.remove("is-visible");
      }
    }
  }

  function validateAttachmentFile(file) {
    if (!file) return "";
    const lowerName = (file.name || "").toLowerCase();
    const dotIdx = lowerName.lastIndexOf(".");
    const ext = dotIdx >= 0 ? lowerName.slice(dotIdx) : "";
    if (!allowedExts.includes(ext)) {
      const allowedLabel = allowedExts.map((e) => e.replace(".", "").toUpperCase()).join(", ");
      return `Unsupported file type. Allowed formats: ${allowedLabel}.`;
    }
    if (file.size <= 0) {
      return "The selected file is empty.";
    }
    if (file.size > maxBytes) {
      const maxMb = (maxBytes / (1024 * 1024)).toFixed(0);
      return `File size exceeds the ${maxMb} MB limit.`;
    }
    return "";
  }

  function validateField(field) {
    const name = field.name;
    const val = (field.value || "").trim();

    if (name === "full_name") {
      if (!val) return "Please enter your full name.";
      if (val.length < 2) return "Full name must be at least 2 characters.";
      if (val.length > 120) return "Full name must be 120 characters or fewer.";
      return "";
    }

    if (name === "email") {
      if (!val) return "Please enter your email address.";
      if (!EMAIL_REGEX.test(val)) return "Enter a valid email address (e.g. you@example.com).";
      return "";
    }

    if (name === "subject") {
      if (!val) return "Please select a subject from the list.";
      return "";
    }

    if (name === "message") {
      if (!val) return "Please enter your message.";
      if (val.length < 10) return "Please write at least 10 characters so we can understand your request.";
      if (val.length > 4000) return "Message cannot exceed 4000 characters.";
      return "";
    }

    if (name === "attachment") {
      const file = field.files && field.files[0];
      return validateAttachmentFile(file);
    }

    return "";
  }

  function updateFilePreview() {
    if (!attachmentInput || !filePreviewEl || !fileNameEl) return;
    const file = attachmentInput.files && attachmentInput.files[0];
    if (file) {
      const sizeKb = Math.max(1, Math.round(file.size / 1024));
      const sizeLabel = sizeKb >= 1024 ? `${(file.size / (1024 * 1024)).toFixed(2)} MB` : `${sizeKb} KB`;
      fileNameEl.textContent = `${file.name} (${sizeLabel})`;
      filePreviewEl.classList.add("is-visible");
    } else {
      fileNameEl.textContent = "";
      filePreviewEl.classList.remove("is-visible");
    }
  }

  function updateCharCount() {
    if (!messageInput || !charCountEl) return;
    charCountEl.textContent = String(messageInput.value.length);
  }

  function renderStatusBanner(type, title, detail) {
    if (!statusRegion) return;
    statusRegion.innerHTML = "";

    const alertDiv = document.createElement("div");
    alertDiv.className = `dsh-alert dsh-alert--${type === "success" ? "success" : "error"}`;
    alertDiv.setAttribute("role", type === "success" ? "status" : "alert");
    alertDiv.setAttribute("tabindex", "-1");

    const icon = document.createElement("i");
    icon.className = `bi ${type === "success" ? "bi-check-circle-fill" : "bi-exclamation-triangle-fill"}`;
    icon.setAttribute("aria-hidden", "true");

    const contentDiv = document.createElement("div");
    const heading = document.createElement("strong");
    heading.className = "d-block mb-1";
    heading.textContent = title;

    const body = document.createElement("p");
    body.className = "mb-0";
    body.textContent = detail;

    contentDiv.appendChild(heading);
    contentDiv.appendChild(body);
    alertDiv.appendChild(icon);
    alertDiv.appendChild(contentDiv);
    statusRegion.appendChild(alertDiv);
    alertDiv.focus({ preventScroll: false });
  }

  function setLoadingState(loading) {
    isSubmitting = loading;
    submitBtn.disabled = loading;
    form.setAttribute("aria-busy", loading ? "true" : "false");
    if (btnSpinner) btnSpinner.classList.toggle("d-none", !loading);
    if (btnText) btnText.textContent = loading ? "Sending..." : "Send Message";
  }

  const controls = Array.from(
    form.querySelectorAll("input:not([type='hidden']):not([name='website']), select, textarea")
  );

  controls.forEach((field) => {
    if (!field.hasAttribute("aria-invalid")) {
      field.setAttribute("aria-invalid", "false");
    }

    field.addEventListener("blur", () => {
      touchedFields.add(field);
      const err = validateField(field);
      setFieldError(field, err);
      if (err) {
        announcer.textContent = err;
      }
    });

    field.addEventListener("input", () => {
      if (field === messageInput) updateCharCount();
      if (touchedFields.has(field) || field.classList.contains("is-invalid")) {
        const err = validateField(field);
        if (!err) setFieldError(field, "");
      }
    });

    field.addEventListener("change", () => {
      touchedFields.add(field);
      if (field === attachmentInput) updateFilePreview();
      const err = validateField(field);
      setFieldError(field, err);
    });
  });

  if (fileClearBtn && attachmentInput) {
    fileClearBtn.addEventListener("click", () => {
      attachmentInput.value = "";
      updateFilePreview();
      setFieldError(attachmentInput, "");
    });
  }

  updateCharCount();
  updateFilePreview();

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    if (isSubmitting) return;

    let firstInvalid = null;
    controls.forEach((field) => {
      touchedFields.add(field);
      const err = validateField(field);
      setFieldError(field, err);
      if (err && !firstInvalid) {
        firstInvalid = field;
      }
    });

    if (firstInvalid) {
      renderStatusBanner(
        "error",
        "Please check your form details",
        "Some required fields need attention before sending."
      );
      firstInvalid.focus();
      return;
    }

    const apiUrl = form.dataset.apiUrl;
    const csrfInput = form.querySelector("input[name='csrfmiddlewaretoken']");
    const csrfToken = csrfInput ? csrfInput.value : "";

    setLoadingState(true);
    if (statusRegion) statusRegion.innerHTML = "";

    try {
      const formData = new FormData(form);
      const response = await fetch(apiUrl, {
        method: "POST",
        body: formData,
        headers: {
          "X-CSRFToken": csrfToken,
          Accept: "application/json",
        },
        credentials: "same-origin",
      });

      let data = {};
      try {
        data = await response.json();
      } catch (_) {
        data = {};
      }

      if (response.ok && data.ok) {
        form.reset();
        controls.forEach((field) => {
          touchedFields.delete(field);
          setFieldError(field, "");
        });
        updateFilePreview();
        updateCharCount();
        renderStatusBanner(
          "success",
          "Message sent successfully",
          data.message || "Thank you! Your message has been received."
        );
        return;
      }

      const serverErrors = data.errors || {};
      let firstServerErrorField = null;
      Object.keys(serverErrors).forEach((fieldName) => {
        const field = form.elements[fieldName];
        const msg = Array.isArray(serverErrors[fieldName])
          ? serverErrors[fieldName][0]
          : String(serverErrors[fieldName]);
        if (field && field.tagName) {
          setFieldError(field, msg);
          if (!firstServerErrorField) firstServerErrorField = field;
        }
      });

      renderStatusBanner(
        "error",
        response.status === 409 ? "Duplicate submission detected" : "Unable to send message",
        data.error || "Please review the highlighted fields and try again."
      );
      if (firstServerErrorField) {
        firstServerErrorField.focus();
      }
    } catch (_) {
      renderStatusBanner(
        "error",
        "Network error",
        "We could not reach the server right now. Please check your connection and try again."
      );
    } finally {
      setLoadingState(false);
    }
  });
})();

