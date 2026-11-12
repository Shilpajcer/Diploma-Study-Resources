import hashlib
import os
import re

from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError

from .models import ContactSubmission

_CONTROL_CHARS_SINGLE_LINE = re.compile(r"[\x00-\x1f\x7f]+")
_CONTROL_CHARS_MULTILINE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]+")
_MULTI_SPACE = re.compile(r"\s+")

_MAGIC_SIGNATURES = {
    ".pdf": lambda head: head.startswith(b"%PDF-"),
    ".png": lambda head: head.startswith(b"\x89PNG\r\n\x1a\n"),
    ".jpg": lambda head: head.startswith(b"\xff\xd8\xff"),
    ".jpeg": lambda head: head.startswith(b"\xff\xd8\xff"),
    ".webp": lambda head: len(head) >= 12 and head[:4] == b"RIFF" and head[8:12] == b"WEBP",
}


def sanitize_plain_text(value, allow_newlines=False):
    """Strip unsafe control characters and normalize whitespace."""
    text = (value or "").replace("\r\n", "\n").replace("\r", "\n")
    if allow_newlines:
        text = _CONTROL_CHARS_MULTILINE.sub("", text)
        return text.strip()
    text = _CONTROL_CHARS_SINGLE_LINE.sub(" ", text)
    return _MULTI_SPACE.sub(" ", text).strip()


def validate_attachment_file(uploaded_file):
    """Validate uploaded attachment extension, size, and file magic bytes."""
    max_bytes = getattr(settings, "CONTACT_MAX_ATTACHMENT_SIZE", 5 * 1024 * 1024)
    allowed_exts = getattr(
        settings,
        "CONTACT_ALLOWED_ATTACHMENT_EXTENSIONS",
        [".pdf", ".png", ".jpg", ".jpeg", ".webp", ".txt"],
    )

    filename = os.path.basename(uploaded_file.name or "")
    _, ext = os.path.splitext(filename)
    ext = ext.lower()

    if ext not in allowed_exts:
        allowed_label = ", ".join(e.lstrip(".").upper() for e in allowed_exts)
        raise ValidationError(
            f"Unsupported file type. Allowed formats: {allowed_label}."
        )

    if uploaded_file.size <= 0:
        raise ValidationError("The attached file appears to be empty.")

    if uploaded_file.size > max_bytes:
        max_mb = max_bytes / (1024 * 1024)
        raise ValidationError(
            f"File is too large. Maximum allowed size is {max_mb:g} MB."
        )

    pos = uploaded_file.tell() if hasattr(uploaded_file, "tell") else 0
    try:
        uploaded_file.seek(0)
        sample = uploaded_file.read(65536)
    finally:
        uploaded_file.seek(pos)

    if ext == ".txt":
        if b"\x00" in sample:
            raise ValidationError("Invalid text file content.")
        try:
            sample.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ValidationError("Text files must be valid UTF-8.") from exc
        return

    signature_check = _MAGIC_SIGNATURES.get(ext)
    if signature_check and not signature_check(sample):
        raise ValidationError(
            "File content does not match the selected file extension."
        )


def compute_submission_hash(email, subject, message):
    """Compute a normalized SHA-256 fingerprint for duplicate detection."""
    normalized = f"{email.strip().lower()}|{subject.strip()}|{message.strip()}"
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


class ContactSubmissionForm(forms.ModelForm):
    """Validates and sanitises contact form submissions."""

    website = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={
                "tabindex": "-1",
                "aria-hidden": "true",
                "autocomplete": "off",
            }
        ),
    )

    class Meta:
        model = ContactSubmission
        fields = ["full_name", "email", "subject", "message", "attachment"]

    def clean_website(self):
        if self.cleaned_data.get("website", "").strip():
            raise ValidationError("Submission blocked by spam protection.")
        return ""

    def clean_full_name(self):
        name = sanitize_plain_text(self.cleaned_data.get("full_name"))
        if len(name) < 2:
            raise ValidationError("Please enter your full name (at least 2 characters).")
        return name

    def clean_email(self):
        raw_email = self.cleaned_data.get("email") or ""
        if "\r" in raw_email or "\n" in raw_email:
            raise ValidationError("Enter a valid email address.")
        return sanitize_plain_text(raw_email).lower()

    def clean_message(self):
        msg = sanitize_plain_text(
            self.cleaned_data.get("message"), allow_newlines=True
        )
        if len(msg.strip()) < 10:
            raise ValidationError(
                "Please enter a message of at least 10 characters."
            )
        return msg

    def clean_attachment(self):
        uploaded_file = self.cleaned_data.get("attachment")
        if uploaded_file:
            validate_attachment_file(uploaded_file)
        return uploaded_file

