from .base import *

# ✅ Режим разработки
DEBUG = True

# ✅ Ключ лучше хранить в .env
SECRET_KEY = config("SECRET_KEY", default="dev-secret-key")

# ✅ Доступ только с localhost
ALLOWED_HOSTS = ["127.0.0.1", "localhost"]

# ✅ Используем SQLite для dev
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# ✅ Email (локально можно консоль)
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"