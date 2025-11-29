#!/usr/bin/env python3
"""
Скрипт для загрузки данных из CSV файла в таблицу ste
"""
import csv
import json
import sys
import os
import logging
from datetime import datetime
from app import create_app, db
from app.models.ste import STE
from sqlalchemy import text

def setup_logging(log_file_path):
    """Настройка логирования в файл"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file_path, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)  # Минимальный вывод в консоль
        ]
    )
    return logging.getLogger(__name__)

def load_csv_to_db(csv_file_path, verbose=False):
    """
    Загружает данные из CSV в таблицу ste
    
    Маппинг столбцов:
    - id → ste_id
    - name → name
    - url → image_url
    - model → model
    - country → country
    - manufacturer → manufacturer
    - category_nm → category
    - filtered_features_json → attributes (JSONB)
    - category_id → игнорируется
    - features → игнорируется
    
    Args:
        csv_file_path: путь к CSV файлу
        verbose: если True, выводит прогресс в консоль
    """
    # Создаем лог файл
    log_dir = os.path.join(os.path.dirname(os.path.abspath(csv_file_path)), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, f'load_csv_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    
    logger = setup_logging(log_file)
    logger.info(f"Начало загрузки данных из {csv_file_path}")
    logger.info(f"Лог файл: {log_file}")
    
    app = create_app()
    
    with app.app_context():
        try:
            
            # Открываем CSV файл
            # Используем utf-8-sig для автоматического удаления BOM (Byte Order Mark)
            with open(csv_file_path, 'r', encoding='utf-8-sig') as f:
                # Определяем разделитель (точка с запятой)
                reader = csv.DictReader(f, delimiter=';')
                
                batch = []
                batch_size = 1000
                total_loaded = 0
                total_errors = 0
                
                for row_num, row in enumerate(reader, start=2):  # Начинаем с 2, так как 1 строка - заголовок
                    try:
                        # Парсим filtered_features_json
                        attributes = {}
                        if row.get('filtered_features_json'):
                            try:
                                # Убираем лишние пробелы и парсим JSON
                                json_str = row['filtered_features_json'].strip()
                                if json_str:
                                    # Декодируем Unicode escape-последовательности
                                    # Если строка содержит \uXXXX, декодируем её
                                    if '\\u' in json_str:
                                        try:
                                            # Пробуем декодировать как Unicode escape
                                            json_str = json_str.encode('utf-8').decode('unicode_escape')
                                        except (UnicodeDecodeError, UnicodeEncodeError):
                                            pass  # Если не получилось, используем как есть
                                    attributes = json.loads(json_str)
                            except (json.JSONDecodeError, UnicodeDecodeError, ValueError) as e:
                                logger.warning(f"Строка {row_num}: не удалось распарсить JSON - {e}")
                                attributes = {}
                        
                        # Создаем словарь для вставки
                        # Если ste_id пустой или None, пропускаем запись (нужен обязательный ID)
                        # Обрабатываем возможный BOM в ключах (например, '\ufeffid' вместо 'id')
                        ste_id = None
                        id_key = 'id'
                        # Проверяем, есть ли ключ с BOM
                        if '\ufeffid' in row:
                            id_key = '\ufeffid'
                        elif 'id' in row:
                            id_key = 'id'
                        
                        if id_key in row and row[id_key] and str(row[id_key]).strip():
                            try:
                                ste_id = int(row[id_key])
                            except (ValueError, TypeError):
                                logger.warning(f"Строка {row_num}: неверный ste_id '{row.get(id_key)}', пропускаю")
                                continue
                        
                        if ste_id is None:
                            logger.warning(f"Строка {row_num}: ste_id отсутствует, пропускаю")
                            continue
                        
                        ste_data = {
                            'ste_id': ste_id,
                            'name': row.get('name', '').strip(),
                            'image_url': row.get('url', '').strip() if row.get('url') else None,
                            'model': row.get('model', '').strip() if row.get('model') else None,
                            'country': row.get('country', '').strip() if row.get('country') else None,
                            'manufacturer': row.get('manufacturer', '').strip() if row.get('manufacturer') else None,
                            'category': row.get('category_nm', '').strip() if row.get('category_nm') else None,
                            'attributes': json.dumps(attributes, ensure_ascii=False),  # Сохраняем Unicode как есть
                            'card_id': None  # При загрузке карточка не привязана
                        }
                        
                        batch.append(ste_data)
                        
                        # Вставляем батчами для производительности
                        if len(batch) >= batch_size:
                            # Используем прямой SQL с явным указанием ste_id
                            # Выполняем каждый элемент батча отдельно, так как executemany не поддерживает jsonb::cast
                            try:
                                for item in batch:
                                    db.session.execute(
                                        text("""
                                            INSERT INTO ste (ste_id, name, image_url, model, country, manufacturer, category, attributes, card_id)
                                            VALUES (:ste_id, :name, :image_url, :model, :country, :manufacturer, :category, CAST(:attributes AS jsonb), :card_id)
                                            ON CONFLICT (ste_id) DO UPDATE SET
                                                name = EXCLUDED.name,
                                                image_url = EXCLUDED.image_url,
                                                model = EXCLUDED.model,
                                                country = EXCLUDED.country,
                                                manufacturer = EXCLUDED.manufacturer,
                                                category = EXCLUDED.category,
                                                attributes = EXCLUDED.attributes
                                        """),
                                        item
                                    )
                                db.session.commit()
                                total_loaded += len(batch)
                                if verbose:
                                    logger.info(f"Загружено {total_loaded} записей...")
                                batch = []
                            except Exception as batch_error:
                                db.session.rollback()  # Откатываем транзакцию при ошибке
                                total_errors += len(batch)
                                logger.error(f"Ошибка при вставке батча (строки {row_num - len(batch) + 1}-{row_num}): {batch_error}")
                                # Пробуем вставить по одному, чтобы найти проблемную запись
                                for item in batch:
                                    try:
                                        db.session.execute(
                                            text("""
                                                INSERT INTO ste (ste_id, name, image_url, model, country, manufacturer, category, attributes, card_id)
                                                VALUES (:ste_id, :name, :image_url, :model, :country, :manufacturer, :category, CAST(:attributes AS jsonb), :card_id)
                                                ON CONFLICT (ste_id) DO UPDATE SET
                                                    name = EXCLUDED.name,
                                                    image_url = EXCLUDED.image_url,
                                                    model = EXCLUDED.model,
                                                    country = EXCLUDED.country,
                                                    manufacturer = EXCLUDED.manufacturer,
                                                    category = EXCLUDED.category,
                                                    attributes = EXCLUDED.attributes
                                            """),
                                            item
                                        )
                                        db.session.commit()
                                        total_loaded += 1
                                    except Exception as item_error:
                                        db.session.rollback()
                                        total_errors += 1
                                        logger.error(f"Ошибка при вставке записи: {item_error}")
                                        logger.error(f"  Данные: {item}")
                                batch = []
                    
                    except Exception as e:
                        total_errors += 1
                        logger.error(f"Ошибка в строке {row_num}: {e}")
                        logger.error(f"  Данные: {row}")
                        # Продолжаем загрузку
                        continue
                
                # Вставляем оставшиеся записи
                if batch:
                    try:
                        for item in batch:
                            db.session.execute(
                                text("""
                                    INSERT INTO ste (ste_id, name, image_url, model, country, manufacturer, category, attributes, card_id)
                                    VALUES (:ste_id, :name, :image_url, :model, :country, :manufacturer, :category, CAST(:attributes AS jsonb), :card_id)
                                    ON CONFLICT (ste_id) DO UPDATE SET
                                        name = EXCLUDED.name,
                                        image_url = EXCLUDED.image_url,
                                        model = EXCLUDED.model,
                                        country = EXCLUDED.country,
                                        manufacturer = EXCLUDED.manufacturer,
                                        category = EXCLUDED.category,
                                        attributes = EXCLUDED.attributes
                                """),
                                item
                            )
                        db.session.commit()
                        total_loaded += len(batch)
                    except Exception as batch_error:
                        db.session.rollback()
                        # Пробуем вставить по одному
                        for item in batch:
                            try:
                                db.session.execute(
                                    text("""
                                        INSERT INTO ste (ste_id, name, image_url, model, country, manufacturer, category, attributes, card_id)
                                        VALUES (:ste_id, :name, :image_url, :model, :country, :manufacturer, :category, CAST(:attributes AS jsonb), :card_id)
                                        ON CONFLICT (ste_id) DO UPDATE SET
                                            name = EXCLUDED.name,
                                            image_url = EXCLUDED.image_url,
                                            model = EXCLUDED.model,
                                            country = EXCLUDED.country,
                                            manufacturer = EXCLUDED.manufacturer,
                                            category = EXCLUDED.category,
                                            attributes = EXCLUDED.attributes
                                    """),
                                    item
                                )
                                db.session.commit()
                                total_loaded += 1
                            except Exception as item_error:
                                db.session.rollback()
                                total_errors += 1
                                logger.error(f"Ошибка при вставке последней записи: {item_error}")
                                logger.error(f"  Данные: {item}")
                
                # Обновляем последовательность ste_id, чтобы она была больше максимального значения
                try:
                    db.session.execute(text("""
                        SELECT setval('ste_ste_id_seq', COALESCE((SELECT MAX(ste_id) FROM ste), 1))
                    """))
                    db.session.commit()
                    logger.info("Последовательность ste_id обновлена")
                except Exception as e:
                    logger.warning(f"Не удалось обновить последовательность ste_id: {e}")
                
                logger.info(f"Загрузка завершена успешно")
                logger.info(f"  Всего загружено: {total_loaded} записей")
                logger.info(f"  Ошибок: {total_errors}")
                logger.info(f"  Лог файл: {log_file}")
                
                if verbose:
                    print(f"\n✓ Загрузка завершена!")
                    print(f"  Всего загружено: {total_loaded} записей")
                    print(f"  Ошибок: {total_errors}")
                    print(f"  Лог файл: {log_file}")
                
        except FileNotFoundError:
            logger.error(f"Файл {csv_file_path} не найден")
            sys.exit(1)
        except Exception as e:
            logger.error(f"Критическая ошибка при загрузке: {e}")
            import traceback
            error_trace = traceback.format_exc()
            logger.error(error_trace)
            db.session.rollback()
            sys.exit(1)

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Загрузка данных из CSV в таблицу ste')
    parser.add_argument('csv_file', help='Путь к CSV файлу')
    parser.add_argument('-v', '--verbose', action='store_true', help='Выводить прогресс в консоль')
    parser.add_argument('--quiet', action='store_true', help='Только критичные сообщения')
    
    args = parser.parse_args()
    
    csv_file = args.csv_file
    if not os.path.exists(csv_file):
        print(f"✗ Файл {csv_file} не найден")
        sys.exit(1)
    
    # Если quiet, отключаем вывод в консоль
    if args.quiet:
        logging.getLogger().handlers = [h for h in logging.getLogger().handlers if not isinstance(h, logging.StreamHandler)]
    
    load_csv_to_db(csv_file, verbose=args.verbose)

