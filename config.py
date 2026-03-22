import os

class Config:
    # ── Database ─────────────────────────────────────────
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "sqlite:///mangal_vows.db"
    )

    # Fix for postgres:// → postgresql://
    if SQLALCHEMY_DATABASE_URI.startswith("postgres://"):
        SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace(
            "postgres://", "postgresql://", 1
        )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ── Security ─────────────────────────────────────────
    SECRET_KEY = os.environ.get("SECRET_KEY") or "dev-secret-key"

    # ── App ──────────────────────────────────────────────
    DEBUG = os.environ.get("DEBUG", "True").lower() == "true"