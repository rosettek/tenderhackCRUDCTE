from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from .config import config

db = SQLAlchemy()
migrate = Migrate()


def create_app(config_name='development'):
    """Фабрика приложения Flask"""
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Инициализация расширений
    db.init_app(app)
    migrate.init_app(app, db)
    CORS(app)
    
    # Регистрация blueprints
    from .routes.cards import cards_bp
    from .routes.features import features_bp
    from .routes.merge import merge_bp
    from .routes.ml import ml_bp
    from .routes.ste import ste_bp
    from .routes import api_bp
    
    app.register_blueprint(cards_bp, url_prefix='/api')
    app.register_blueprint(features_bp, url_prefix='/api')
    app.register_blueprint(merge_bp, url_prefix='/api')
    app.register_blueprint(ml_bp, url_prefix='/api')
    app.register_blueprint(ste_bp, url_prefix='/api')
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # Тестовый маршрут
    @app.route('/health')
    def health_check():
        return {'status': 'ok', 'message': 'Backend is running'}
    
    return app

