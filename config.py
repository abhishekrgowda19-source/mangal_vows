import os


class Config:

    SECRET_KEY = os.environ.get("SECRET_KEY", "mangal_secret_key")

    database_url = os.environ.get("DATABASE_URL")

    # Fix old postgres:// prefix used by some platforms
    if database_url:
        database_url = database_url.replace("postgres://", "postgresql://", 1)

    SQLALCHEMY_DATABASE_URI = database_url or "sqlite:///mangal_vows.db"

    SQLALCHEMY_TRACK_MODIFICATIONS = False