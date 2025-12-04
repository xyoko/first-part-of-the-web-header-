import os
from dotenv import load_dotenv
load_dotenv()


class BaseConfig:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///dev.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'False').lower() == 'true'
    SESSION_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SECURE = os.environ.get('REMEMBER_COOKIE_SECURE', 'False').lower() == 'true'
    MAX_CONTENT_LENGTH = 8 * 1024 * 1024


class DevelopmentConfig(BaseConfig):
    DEBUG = True


class ProductionConfig(BaseConfig):
    DEBUG = False
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True


# Provide a `Config` name for backward compatibility with app imports.
# Select ProductionConfig when FLASK_ENV indicates production, otherwise DevelopmentConfig.
_env = os.environ.get('FLASK_ENV', os.environ.get('ENV', '')).lower()
if _env in ('production', 'prod'):
    Config = ProductionConfig
else:
    Config = DevelopmentConfig
