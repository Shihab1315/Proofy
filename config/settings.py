# config/settings.py

"""
Django settings for the Proofly project.

Proofly — Digital Evidence & Complaint Management Platform
Phase 01: Project configuration & custom user model.
"""

from pathlib import Path
import os

# ------------------------------------------------------------------------------
# BASE DIRECTORY
# ------------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent

# ------------------------------------------------------------------------------
# SECURITY
# ------------------------------------------------------------------------------
# Development: fallback values are provided so the project runs immediately.
# Production: set these as real environment variables.

SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY",
    "django-insecure-proofly-development-key-change-me-before-production",
)

# DEBUG stays True for local development. In production, set DEBUG=False
# as an environment variable.
DEBUG = os.environ.get("DJANGO_DEBUG", "True").lower() in ("1", "true", "yes")

ALLOWED_HOSTS = [
    host.strip()
    for host in os.environ.get("DJANGO_ALLOWED_HOSTS", "127.0.0.1,localhost").split(",")
    if host.strip()
]

# ------------------------------------------------------------------------------
# APPLICATIONS
# ------------------------------------------------------------------------------

INSTALLED_APPS = [
    # Django built-in apps
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Proofly apps
    "accounts.apps.AccountsConfig",
    "complaints.apps.ComplaintsConfig",
    "dashboard.apps.DashboardConfig",
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

# ------------------------------------------------------------------------------
# TEMPLATES
# ------------------------------------------------------------------------------

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
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# ------------------------------------------------------------------------------
# DATABASE — SQLite for development
# ------------------------------------------------------------------------------

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# ------------------------------------------------------------------------------
# PASSWORD VALIDATION
# ------------------------------------------------------------------------------

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# ------------------------------------------------------------------------------
# CUSTOM USER MODEL
# ------------------------------------------------------------------------------
# This must be set before the first migration is applied.
# Once migrations exist, changing this setting requires a database reset
# or a carefully planned migration.

AUTH_USER_MODEL = "accounts.User"

# ------------------------------------------------------------------------------
# INTERNATIONALIZATION
# ------------------------------------------------------------------------------

LANGUAGE_CODE = "en-us"

TIME_ZONE = "Asia/Dhaka"

USE_I18N = True

USE_TZ = True

# ------------------------------------------------------------------------------
# STATIC FILES (CSS, JavaScript, images used by the site itself)
# ------------------------------------------------------------------------------

STATIC_URL = "static/"

STATICFILES_DIRS = [
    BASE_DIR / "static",
]

STATIC_ROOT = BASE_DIR / "staticfiles"

# ------------------------------------------------------------------------------
# MEDIA FILES (user-uploaded complaint evidence)
# ------------------------------------------------------------------------------

MEDIA_URL = "media/"

MEDIA_ROOT = BASE_DIR / "media"

# ------------------------------------------------------------------------------
# AUTHENTICATION REDIRECTS
# ------------------------------------------------------------------------------
# These URLs will be used in later phases when login/logout views are built.

LOGIN_URL = "accounts:login"

LOGIN_REDIRECT_URL = "dashboard:home"

LOGOUT_REDIRECT_URL = "accounts:login"

# ------------------------------------------------------------------------------
# DEFAULT PRIMARY KEY
# ------------------------------------------------------------------------------

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"