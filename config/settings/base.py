"""Settings shared by every environment. No secrets in this file."""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Load optional local .env file (git-ignored) for SMTP and environment overrides
_env_file = BASE_DIR / ".env"
if _env_file.exists():
    try:
        with open(_env_file, "r", encoding="utf-8") as _f:
            for _line in _f:
                _line = _line.strip()
                if _line and not _line.startswith("#") and "=" in _line:
                    _k, _v = _line.split("=", 1)
                    os.environ.setdefault(_k.strip(), _v.strip().strip("'\""))
    except Exception:
        pass

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "apps.core",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.core.context_processors.site",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-in"
TIME_ZONE = "Asia/Kolkata"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ---- Site-level settings -------------------------------------------------
SITE_NAME = "Diploma Study Hub"

# Feature flags: V1 launches with everything below set to False.
# Flip a flag to True when that version's feature is built and tested.
FEATURE_FLAGS = {
    "student_accounts": False,       # V2: login / register / dashboard
    "student_contributions": False,  # V2: upload + moderation
    "material_requests": False,      # V2: missing material form
}

# ---- Contact & Email settings (configured via environment variables) -------
CONTACT_INFO = {
    "general_email": os.environ.get("CONTACT_GENERAL_EMAIL", "").strip(),
    "support_email": os.environ.get("CONTACT_SUPPORT_EMAIL", "").strip(),
    "materials_email": os.environ.get("CONTACT_MATERIALS_EMAIL", "").strip(),
    "feedback_email": os.environ.get("CONTACT_FEEDBACK_EMAIL", "").strip(),
    "support_phone": os.environ.get("CONTACT_PHONE", "").strip(),
    "office_address": os.environ.get("CONTACT_ADDRESS", "").strip(),
    "admin_notification_email": os.environ.get("CONTACT_ADMIN_EMAIL", "").strip(),
}

CONTACT_MAX_ATTACHMENT_SIZE = int(
    os.environ.get("CONTACT_MAX_ATTACHMENT_SIZE", 5 * 1024 * 1024)
)
CONTACT_ALLOWED_ATTACHMENT_EXTENSIONS = [
    ".pdf",
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
    ".txt",
]

EMAIL_CONFIGURED = bool(
    os.environ.get("EMAIL_HOST", "").strip()
    or os.environ.get("DJANGO_EMAIL_BACKEND", "").strip()
)
EMAIL_BACKEND = os.environ.get(
    "DJANGO_EMAIL_BACKEND",
    "django.core.mail.backends.smtp.EmailBackend"
    if os.environ.get("EMAIL_HOST", "").strip()
    else "django.core.mail.backends.dummy.EmailBackend",
)
EMAIL_HOST = os.environ.get("EMAIL_HOST", "")
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", "587"))
EMAIL_USE_TLS = os.environ.get("EMAIL_USE_TLS", "True").lower() in ("1", "true", "yes")
EMAIL_USE_SSL = os.environ.get("EMAIL_USE_SSL", "False").lower() in ("1", "true", "yes")
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")
DEFAULT_FROM_EMAIL = os.environ.get(
    "DEFAULT_FROM_EMAIL",
    CONTACT_INFO["general_email"] or "noreply@localhost",
)
