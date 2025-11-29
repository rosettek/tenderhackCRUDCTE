import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Конфигурация приложения"""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key')
    
    # Database (PostgreSQL по умолчанию, можно переопределить через DATABASE_URL)
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL', 
        'postgresql://postgres:postgres@localhost:5432/tenderhack'  # PostgreSQL по умолчанию
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = os.environ.get('SQL_ECHO', 'false').lower() == 'true'
    
    # Настройки пула соединений для стабильной работы с PostgreSQL
    # Flask-SQLAlchemy автоматически использует эти настройки
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_recycle': 3600,
        'pool_pre_ping': True,  # Проверка соединения перед использованием
        'max_overflow': 20,
        'connect_args': {
            'connect_timeout': 10,
            'application_name': 'tenderhack_backend'
        }
    }


class DevelopmentConfig(Config):
    """Конфигурация для разработки"""
    DEBUG = True


class ProductionConfig(Config):
    """Конфигурация для продакшена"""
    DEBUG = False


class TestingConfig(Config):
    """Конфигурация для тестирования"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

