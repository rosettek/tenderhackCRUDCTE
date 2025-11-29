#!/usr/bin/env python3
"""
Скрипт для инициализации базы данных
Создает таблицы из init.sql или через SQLAlchemy
"""
from app import create_app, db
from app.models import Card, STE, CardSignificantFeature

def init_database():
    """Создать все таблицы в базе данных"""
    app = create_app()
    
    with app.app_context():
        # Создаем все таблицы
        db.create_all()
        print("✓ Таблицы созданы успешно")
        
        # Проверяем, что таблицы существуют
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        print(f"✓ Создано таблиц: {len(tables)}")
        for table in tables:
            print(f"  - {table}")

if __name__ == '__main__':
    init_database()

