import os


class Config:
    # ── Database ──────────────────────────────────────────────────────────────
    # Use PostgreSQL in production, SQLite for local dev
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "sqlite:///mangal_vows.db"   # fallback for local dev
    )
    # Fix Heroku/Render postgres:// → postgresql://
    if SQLALCHEMY_DATABASE_URI.startswith("postgres://"):
        SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace(
            "postgres://", "postgresql://", 1
        )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ── Security ──────────────────────────────────────────────────────────────
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-in-production")

    # ── Razorpay ─────────────────────────────────────────────────────────────
    RAZORPAY_KEY_ID      = os.environ.get("RAZORPAY_KEY_ID", "")
    RAZORPAY_KEY_SECRET  = os.environ.get("RAZORPAY_KEY_SECRET", "")
    RAZORPAY_WEBHOOK_SECRET = os.environ.get("RAZORPAY_WEBHOOK_SECRET", "")

    # ── Admin ─────────────────────────────────────────────────────────────────
    ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "")   # must be set in env

    # ── App ───────────────────────────────────────────────────────────────────
    DEBUG = os.environ.get("DEBUG", "False") == "True"