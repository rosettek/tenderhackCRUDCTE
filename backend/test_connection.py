#!/usr/bin/env python3
"""
Тестовый скрипт для проверки подключения к БД и наличия таблиц
"""
from app import create_app, db
from app.models import Card, STE, CardSignificantFeature
from sqlalchemy import inspect, text

def test_connection():
    app = create_app()
    
    with app.app_context():
        try:
            # Проверяем подключение
            result = db.session.execute(text('SELECT 1'))
            print("✓ Подключение к БД успешно")
            
            # Проверяем наличие таблиц
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            print(f"✓ Найдено таблиц: {len(tables)}")
            for table in tables:
                print(f"  - {table}")
            
            # Проверяем наличие таблицы cards
            if 'cards' in tables:
                print("✓ Таблица 'cards' существует")
                # Пробуем выполнить запрос
                count = Card.query.count()
                print(f"✓ Запрос выполнен успешно. Карточек в БД: {count}")
            else:
                print("✗ Таблица 'cards' НЕ существует")
                print("  Создаю таблицы...")
                db.create_all()
                print("✓ Таблицы созданы")
                
        except Exception as e:
            print(f"✗ Ошибка: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    test_connection()

