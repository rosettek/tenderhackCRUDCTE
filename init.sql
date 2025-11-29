-- =====================================================
-- Инициализация базы данных TenderHack
-- =====================================================


-- Карточки
CREATE TABLE IF NOT EXISTS cards (
    card_id SERIAL PRIMARY KEY,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);


-- СТЕ (Стандартные товарные единицы)
CREATE TABLE IF NOT EXISTS ste (
    ste_id SERIAL PRIMARY KEY,
    card_id INT REFERENCES cards(card_id) ON DELETE SET NULL,
    name VARCHAR NOT NULL,
    image_url VARCHAR,
    model  VARCHAR,
    manufacturer  VARCHAR,
    country VARCHAR,
    category VARCHAR,
    -- Все атрибуты СТЕ в формате {"feature_name": "value", ...}
    attributes JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Значимые характеристики карточки (список названий характеристик, которые определяют группировку)
-- Это главная таблица! Изменение этого списка = пересоздание карточек
CREATE TABLE IF NOT EXISTS card_significant_features (
    id SERIAL PRIMARY KEY,
    card_id INT NOT NULL REFERENCES cards(card_id) ON DELETE CASCADE,
    feature_name VARCHAR(255) NOT NULL,
    display_order INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(card_id, feature_name)
);



CREATE TABLE IF NOT EXISTS CHANGE_GROUP_LOG (
    ste_id INT NOT NULL REFERENCES  ste(ste_id),
    new_card_id INT NOT NULL REFERENCES cards(card_id),
    change_date TIMESTAMP
);
