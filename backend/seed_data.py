"""
Скрипт для заполнения базы данных тестовыми данными
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import Category, Card, STE, CardFeature, CategoryFeatureSignificance

app = create_app()

# Тестовые данные
CATEGORIES = [
    {"name": "Электроника", "parent_id": None},
    {"name": "Смартфоны", "parent_id": 1},
    {"name": "Ноутбуки", "parent_id": 1},
    {"name": "Аксессуары", "parent_id": 1},
    {"name": "Бытовая техника", "parent_id": None},
    {"name": "Холодильники", "parent_id": 5},
    {"name": "Стиральные машины", "parent_id": 5},
]

CARDS = [
    {
        "title": "Samsung Galaxy S21",
        "description": "Флагманский смартфон Samsung 2021 года",
        "category_id": 2,
        "features": [
            {"name": "Производитель", "value": "Samsung", "significant": True, "weight": 1.0},
            {"name": "Модель", "value": "Galaxy S21", "significant": True, "weight": 0.95},
            {"name": "Диагональ экрана", "value": "6.2 дюйма", "significant": True, "weight": 0.9},
            {"name": "Оперативная память", "value": "8 ГБ", "significant": True, "weight": 0.85},
            {"name": "Встроенная память", "value": "128 ГБ", "significant": True, "weight": 0.8},
            {"name": "Цвет", "value": "Phantom Gray", "significant": False, "weight": 0.2},
        ]
    },
    {
        "title": "iPhone 14 Pro",
        "description": "Флагманский смартфон Apple 2022 года",
        "category_id": 2,
        "features": [
            {"name": "Производитель", "value": "Apple", "significant": True, "weight": 1.0},
            {"name": "Модель", "value": "iPhone 14 Pro", "significant": True, "weight": 0.95},
            {"name": "Диагональ экрана", "value": "6.1 дюйма", "significant": True, "weight": 0.9},
            {"name": "Оперативная память", "value": "6 ГБ", "significant": True, "weight": 0.85},
            {"name": "Встроенная память", "value": "256 ГБ", "significant": True, "weight": 0.8},
            {"name": "Цвет", "value": "Deep Purple", "significant": False, "weight": 0.2},
        ]
    },
    {
        "title": "MacBook Pro 14",
        "description": "Профессиональный ноутбук Apple с чипом M2 Pro",
        "category_id": 3,
        "features": [
            {"name": "Производитель", "value": "Apple", "significant": True, "weight": 1.0},
            {"name": "Модель", "value": "MacBook Pro 14", "significant": True, "weight": 0.95},
            {"name": "Процессор", "value": "Apple M2 Pro", "significant": True, "weight": 0.9},
            {"name": "Оперативная память", "value": "16 ГБ", "significant": True, "weight": 0.85},
            {"name": "SSD", "value": "512 ГБ", "significant": True, "weight": 0.8},
            {"name": "Диагональ экрана", "value": "14.2 дюйма", "significant": True, "weight": 0.75},
        ]
    },
    {
        "title": "Lenovo ThinkPad X1 Carbon",
        "description": "Бизнес-ноутбук премиум класса",
        "category_id": 3,
        "features": [
            {"name": "Производитель", "value": "Lenovo", "significant": True, "weight": 1.0},
            {"name": "Модель", "value": "ThinkPad X1 Carbon Gen 11", "significant": True, "weight": 0.95},
            {"name": "Процессор", "value": "Intel Core i7-1365U", "significant": True, "weight": 0.9},
            {"name": "Оперативная память", "value": "16 ГБ", "significant": True, "weight": 0.85},
            {"name": "SSD", "value": "512 ГБ", "significant": True, "weight": 0.8},
            {"name": "Диагональ экрана", "value": "14 дюймов", "significant": True, "weight": 0.75},
        ]
    },
    {
        "title": "Samsung Galaxy Watch 6",
        "description": "Умные часы Samsung",
        "category_id": 4,
        "features": [
            {"name": "Производитель", "value": "Samsung", "significant": True, "weight": 1.0},
            {"name": "Модель", "value": "Galaxy Watch 6", "significant": True, "weight": 0.95},
            {"name": "Размер корпуса", "value": "44 мм", "significant": True, "weight": 0.8},
            {"name": "Цвет", "value": "Graphite", "significant": False, "weight": 0.2},
        ]
    },
]

# СТЕ привязанные к карточкам
STES_ASSIGNED = [
    # Samsung Galaxy S21
    {"name": "Samsung Galaxy S21 128GB Phantom Gray", "card_id": 1, "attributes": {"color": "Phantom Gray", "memory": "128GB", "condition": "new"}},
    {"name": "Samsung Galaxy S21 256GB Phantom White", "card_id": 1, "attributes": {"color": "Phantom White", "memory": "256GB", "condition": "new"}},
    {"name": "Samsung Galaxy S21 128GB Phantom Pink", "card_id": 1, "attributes": {"color": "Phantom Pink", "memory": "128GB", "condition": "refurbished"}},
    
    # iPhone 14 Pro
    {"name": "iPhone 14 Pro 256GB Deep Purple", "card_id": 2, "attributes": {"color": "Deep Purple", "memory": "256GB", "condition": "new"}},
    {"name": "iPhone 14 Pro 512GB Space Black", "card_id": 2, "attributes": {"color": "Space Black", "memory": "512GB", "condition": "new"}},
    {"name": "iPhone 14 Pro 256GB Gold", "card_id": 2, "attributes": {"color": "Gold", "memory": "256GB", "condition": "new"}},
    {"name": "iPhone 14 Pro 128GB Silver", "card_id": 2, "attributes": {"color": "Silver", "memory": "128GB", "condition": "refurbished"}},
    
    # MacBook Pro 14
    {"name": "MacBook Pro 14 M2 Pro 16GB 512GB Space Gray", "card_id": 3, "attributes": {"chip": "M2 Pro", "ram": "16GB", "ssd": "512GB", "color": "Space Gray"}},
    {"name": "MacBook Pro 14 M2 Pro 32GB 1TB Silver", "card_id": 3, "attributes": {"chip": "M2 Pro", "ram": "32GB", "ssd": "1TB", "color": "Silver"}},
    
    # ThinkPad X1 Carbon
    {"name": "ThinkPad X1 Carbon Gen 11 i7 16GB 512GB", "card_id": 4, "attributes": {"cpu": "i7-1365U", "ram": "16GB", "ssd": "512GB"}},
    {"name": "ThinkPad X1 Carbon Gen 11 i5 8GB 256GB", "card_id": 4, "attributes": {"cpu": "i5-1345U", "ram": "8GB", "ssd": "256GB"}},
    
    # Galaxy Watch 6
    {"name": "Samsung Galaxy Watch 6 44mm Graphite", "card_id": 5, "attributes": {"size": "44mm", "color": "Graphite"}},
    {"name": "Samsung Galaxy Watch 6 40mm Gold", "card_id": 5, "attributes": {"size": "40mm", "color": "Gold"}},
]

# Нераспределённые СТЕ (без карточки)
STES_UNASSIGNED = [
    {"name": "Xiaomi 13 Pro 256GB Black", "card_id": None, "attributes": {"brand": "Xiaomi", "model": "13 Pro", "memory": "256GB", "color": "Black"}},
    {"name": "Xiaomi 13 Pro 512GB White", "card_id": None, "attributes": {"brand": "Xiaomi", "model": "13 Pro", "memory": "512GB", "color": "White"}},
    {"name": "Google Pixel 8 Pro 128GB Obsidian", "card_id": None, "attributes": {"brand": "Google", "model": "Pixel 8 Pro", "memory": "128GB", "color": "Obsidian"}},
    {"name": "Google Pixel 8 256GB Hazel", "card_id": None, "attributes": {"brand": "Google", "model": "Pixel 8", "memory": "256GB", "color": "Hazel"}},
    {"name": "OnePlus 12 256GB Flowy Emerald", "card_id": None, "attributes": {"brand": "OnePlus", "model": "12", "memory": "256GB", "color": "Flowy Emerald"}},
    {"name": "ASUS ROG Zephyrus G14 RTX 4060", "card_id": None, "attributes": {"brand": "ASUS", "model": "ROG Zephyrus G14", "gpu": "RTX 4060", "ram": "16GB"}},
    {"name": "Dell XPS 15 i7 32GB 1TB", "card_id": None, "attributes": {"brand": "Dell", "model": "XPS 15", "cpu": "i7-13700H", "ram": "32GB", "ssd": "1TB"}},
    {"name": "HP Spectre x360 16 i7 16GB", "card_id": None, "attributes": {"brand": "HP", "model": "Spectre x360 16", "cpu": "i7-1360P", "ram": "16GB"}},
    {"name": "AirPods Pro 2nd Gen", "card_id": None, "attributes": {"brand": "Apple", "model": "AirPods Pro", "generation": "2nd"}},
    {"name": "Sony WH-1000XM5 Black", "card_id": None, "attributes": {"brand": "Sony", "model": "WH-1000XM5", "color": "Black", "type": "headphones"}},
    {"name": "Logitech MX Master 3S", "card_id": None, "attributes": {"brand": "Logitech", "model": "MX Master 3S", "type": "mouse"}},
    {"name": "Samsung T7 Shield 2TB", "card_id": None, "attributes": {"brand": "Samsung", "model": "T7 Shield", "capacity": "2TB", "type": "ssd"}},
]

# Значимость характеристик по категориям
CATEGORY_SIGNIFICANCE = [
    # Смартфоны (category_id=2)
    {"category_id": 2, "feature_name": "Производитель", "is_significant": True},
    {"category_id": 2, "feature_name": "Модель", "is_significant": True},
    {"category_id": 2, "feature_name": "Диагональ экрана", "is_significant": True},
    {"category_id": 2, "feature_name": "Оперативная память", "is_significant": True},
    {"category_id": 2, "feature_name": "Встроенная память", "is_significant": True},
    {"category_id": 2, "feature_name": "Цвет", "is_significant": False},
    {"category_id": 2, "feature_name": "Состояние", "is_significant": False},
    
    # Ноутбуки (category_id=3)
    {"category_id": 3, "feature_name": "Производитель", "is_significant": True},
    {"category_id": 3, "feature_name": "Модель", "is_significant": True},
    {"category_id": 3, "feature_name": "Процессор", "is_significant": True},
    {"category_id": 3, "feature_name": "Оперативная память", "is_significant": True},
    {"category_id": 3, "feature_name": "SSD", "is_significant": True},
    {"category_id": 3, "feature_name": "Диагональ экрана", "is_significant": True},
    {"category_id": 3, "feature_name": "Цвет", "is_significant": False},
]


def seed_database():
    """Заполнить базу данных тестовыми данными"""
    with app.app_context():
        print("Очистка базы данных...")
        # Очищаем таблицы в правильном порядке
        db.session.query(CardFeature).delete()
        db.session.query(STE).delete()
        db.session.query(Card).delete()
        db.session.query(CategoryFeatureSignificance).delete()
        db.session.query(Category).delete()
        db.session.commit()
        
        print("Создание категорий...")
        for cat_data in CATEGORIES:
            category = Category(
                name=cat_data["name"],
                parent_id=cat_data["parent_id"]
            )
            db.session.add(category)
        db.session.commit()
        print(f"  Создано категорий: {len(CATEGORIES)}")
        
        print("Создание карточек и характеристик...")
        for card_data in CARDS:
            card = Card(
                title=card_data["title"],
                description=card_data["description"],
                category_id=card_data["category_id"]
            )
            db.session.add(card)
            db.session.flush()  # Получаем card_id
            
            # Добавляем характеристики
            for feature in card_data["features"]:
                card_feature = CardFeature(
                    card_id=card.card_id,
                    feature_name=feature["name"],
                    feature_value=feature["value"],
                    is_significant=feature["significant"],
                    significance_weight=feature["weight"]
                )
                db.session.add(card_feature)
        
        db.session.commit()
        print(f"  Создано карточек: {len(CARDS)}")
        
        print("Создание СТЕ (привязанных к карточкам)...")
        for ste_data in STES_ASSIGNED:
            ste = STE(
                name=ste_data["name"],
                card_id=ste_data["card_id"],
                attributes=ste_data["attributes"]
            )
            db.session.add(ste)
        db.session.commit()
        print(f"  Создано привязанных СТЕ: {len(STES_ASSIGNED)}")
        
        print("Создание СТЕ (нераспределённых)...")
        for ste_data in STES_UNASSIGNED:
            ste = STE(
                name=ste_data["name"],
                card_id=ste_data["card_id"],
                attributes=ste_data["attributes"]
            )
            db.session.add(ste)
        db.session.commit()
        print(f"  Создано нераспределённых СТЕ: {len(STES_UNASSIGNED)}")
        
        print("Создание настроек значимости по категориям...")
        for sig_data in CATEGORY_SIGNIFICANCE:
            significance = CategoryFeatureSignificance(
                category_id=sig_data["category_id"],
                feature_name=sig_data["feature_name"],
                is_significant=sig_data["is_significant"],
                updated_by=1
            )
            db.session.add(significance)
        db.session.commit()
        print(f"  Создано настроек значимости: {len(CATEGORY_SIGNIFICANCE)}")
        
        print("\n" + "="*50)
        print("База данных успешно заполнена!")
        print("="*50)
        
        # Статистика
        print(f"\nСтатистика:")
        print(f"  - Категорий: {Category.query.count()}")
        print(f"  - Карточек: {Card.query.count()}")
        print(f"  - Характеристик: {CardFeature.query.count()}")
        print(f"  - СТЕ всего: {STE.query.count()}")
        print(f"  - СТЕ привязанных: {STE.query.filter(STE.card_id.isnot(None)).count()}")
        print(f"  - СТЕ нераспределённых: {STE.query.filter(STE.card_id.is_(None)).count()}")


if __name__ == "__main__":
    seed_database()


