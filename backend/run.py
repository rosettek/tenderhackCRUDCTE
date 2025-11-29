import sys
import os
import argparse
from sqlalchemy import text, inspect
from app import create_app, db

def drop_all_tables():
    """Удаляет все таблицы из БД"""
    app = create_app()
    with app.app_context():
        try:
            print("Удаляю все таблицы...")
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            
            if not tables:
                print("  Таблиц не найдено")
                return
            
            print(f"  Найдено таблиц: {len(tables)}")
            for table in tables:
                print(f"    - {table}")
            
            # Отключаем проверку внешних ключей для безопасного удаления
            db.session.execute(text('SET session_replication_role = replica;'))
            
            # Удаляем все таблицы через CASCADE (автоматически удаляет зависимости)
            for table in tables:
                db.session.execute(text(f'DROP TABLE IF EXISTS "{table}" CASCADE;'))
            
            db.session.commit()
            print("✓ Все таблицы удалены")
        except Exception as e:
            db.session.rollback()
            print(f"✗ Ошибка при удалении таблиц: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)

def execute_init_sql():
    """Выполняет init.sql"""
    app = create_app()
    
    # Путь к init.sql относительно корня проекта
    init_sql_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'init.sql')
    
    if not os.path.exists(init_sql_path):
        print(f"✗ Файл {init_sql_path} не найден")
        sys.exit(1)
    
    with app.app_context():
        try:
            print(f"Выполняю {init_sql_path}...")
            
            with open(init_sql_path, 'r', encoding='utf-8') as f:
                sql_content = f.read()
            
            # Выполняем весь SQL файл целиком
            # PostgreSQL может обработать многострочные конструкции (DO $$ ... $$;)
            db.session.execute(text(sql_content))
            db.session.commit()
            print("✓ init.sql выполнен успешно")
            
        except Exception as e:
            db.session.rollback()
            # Игнорируем ошибки "already exists" для IF NOT EXISTS
            error_str = str(e).lower()
            if 'already exists' in error_str or 'duplicate' in error_str:
                print("✓ init.sql выполнен (некоторые объекты уже существуют)")
            else:
                print(f"✗ Ошибка при выполнении init.sql: {e}")
                import traceback
                traceback.print_exc()
                sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description='Запуск Flask приложения')
    parser.add_argument('-d', '--drop', action='store_true', 
                       help='Удалить все таблицы и выполнить init.sql заново')
    
    args = parser.parse_args()
    
    if args.drop:
        print("=" * 50)
        print("Режим пересоздания БД (-d)")
        print("=" * 50)
        drop_all_tables()
        execute_init_sql()
        print("=" * 50)
        print("БД пересоздана. Запускаю приложение...")
        print("=" * 50)
    
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)

if __name__ == '__main__':
    main()

