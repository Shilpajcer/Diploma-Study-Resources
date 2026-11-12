from .base import *  # noqa: F401,F403
import os

DEBUG = True
ALLOWED_HOSTS = ["localhost", "127.0.0.1"]
# Media files (uploaded documents)
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# Dev-only key. Production (prod.py, Phase 14) must read a real secret from the environment.
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "dev-only-insecure-key-do-not-use-in-production")

# SQLite is only a stand-in for Phase 2. We switch to MySQL in Phase 4.
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",  # noqa: F405
    }
}
X_FRAME_OPTIONS = "SAMEORIGIN"

# Development-only local email capture (writes emails to sent_emails/ instead of sending over SMTP).
# Public Contact Us cards remain unconfigured unless CONTACT_* env vars are set.
if not os.environ.get("EMAIL_HOST", "").strip() and not os.environ.get("DJANGO_EMAIL_BACKEND", "").strip():
    EMAIL_CONFIGURED = True
    EMAIL_BACKEND = "django.core.mail.backends.filebased.EmailBackend"
    EMAIL_FILE_PATH = BASE_DIR / "sent_emails"  # noqa: F405

if not CONTACT_INFO.get("admin_notification_email"):  # noqa: F405
    CONTACT_INFO = {**CONTACT_INFO, "admin_notification_email": "sandeshbhivase96@gmail.com"}  # noqa: F405