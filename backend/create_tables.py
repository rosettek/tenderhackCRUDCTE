#!/usr/bin/env python3
"""
Скрипт для создания таблиц в базе данных
"""
import sys
import os

# Добавляем путь к приложению
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import Card, STE, CardSignificantFeature

def main():
    app = create_app()
    
    with app.app_context():
        try:
            print("Проверяю подключение к БД...")
            db.session.execute(db.text('SELECT 1'))
            print("✓ Подключение успешно")
            
            print("Создаю таблицы...")
            db.create_all()
            print("✓ Таблицы созданы")
            
            # Проверяем наличие таблиц
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            print(f"\n✓ Создано таблиц: {len(tables)}")
            for table in tables:
                print(f"  - {table}")
                
        except Exception as e:
            print(f"✗ Ошибка: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)

if __name__ == '__main__':
    main()

