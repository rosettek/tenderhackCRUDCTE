-- =====================================================
-- Инициализация базы данных TenderHack
-- =====================================================

-- Категории
CREATE TABLE IF NOT EXISTS categories (
    category_id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    parent_id INT REFERENCES categories(category_id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Карточки
CREATE TABLE IF NOT EXISTS cards (
    card_id SERIAL PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    category_id INT REFERENCES categories(category_id),
    -- Хэш значимых характеристик для быстрого поиска дубликатов
    significant_features_hash VARCHAR(64),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

CREATE INDEX IF NOT EXISTS idx_cards_sig_hash ON cards(significant_features_hash) WHERE is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_cards_category ON cards(category_id) WHERE is_active = TRUE;

-- СТЕ (Стандартные товарные единицы)
CREATE TABLE IF NOT EXISTS ste (
    ste_id SERIAL PRIMARY KEY,
    card_id INT REFERENCES cards(card_id) ON DELETE SET NULL,
    name VARCHAR(500) NOT NULL,
    -- Все атрибуты СТЕ в формате {"feature_name": "value", ...}
    attributes JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_ste_card_id ON ste(card_id);
CREATE INDEX IF NOT EXISTS idx_ste_attributes ON ste USING GIN(attributes);

-- Значимые характеристики карточки (список названий характеристик, которые определяют группировку)
-- Это главная таблица! Изменение этого списка = пересоздание карточек
CREATE TABLE IF NOT EXISTS card_significant_features (
    id SERIAL PRIMARY KEY,
    card_id INT NOT NULL REFERENCES cards(card_id) ON DELETE CASCADE,
    feature_name VARCHAR(255) NOT NULL,
    -- Значение этой характеристики (вычисляется из СТЕ)
    feature_value VARCHAR(1000),
    display_order INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(card_id, feature_name)
);

CREATE INDEX IF NOT EXISTS idx_card_sig_features_card ON card_significant_features(card_id);
CREATE INDEX IF NOT EXISTS idx_card_sig_features_name ON card_significant_features(feature_name);

-- Шаблоны значимых характеристик по категориям (для подсказок, не влияет на группировку)
CREATE TABLE IF NOT EXISTS category_feature_templates (
    id SERIAL PRIMARY KEY,
    category_id INT NOT NULL REFERENCES categories(category_id) ON DELETE CASCADE,
    feature_name VARCHAR(255) NOT NULL,
    is_recommended_significant BOOLEAN DEFAULT TRUE,
    usage_count INT DEFAULT 0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(category_id, feature_name)
);

-- Логи изменений характеристик
CREATE TYPE feature_operation AS ENUM (
    'mark_significant',
    'mark_insignificant',
    'change_value',
    'add_feature',
    'remove_feature'
);

CREATE TABLE IF NOT EXISTS feature_change_logs (
    log_id SERIAL PRIMARY KEY,
    operation feature_operation NOT NULL,
    ste_id INT REFERENCES ste(ste_id) ON DELETE SET NULL,
    card_id INT NOT NULL REFERENCES cards(card_id) ON DELETE CASCADE,
    category_id INT REFERENCES categories(category_id) ON DELETE SET NULL,
    feature_name VARCHAR(255) NOT NULL,
    old_value VARCHAR(1000),
    new_value VARCHAR(1000),
    became_significant BOOLEAN,
    became_insignificant BOOLEAN,
    moderator_id INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    comment TEXT
);

CREATE INDEX IF NOT EXISTS idx_feature_logs_card ON feature_change_logs(card_id);
CREATE INDEX IF NOT EXISTS idx_feature_logs_operation ON feature_change_logs(operation);
CREATE INDEX IF NOT EXISTS idx_feature_logs_created ON feature_change_logs(created_at);

-- Логи объединения карточек
CREATE TABLE IF NOT EXISTS card_merge_logs (
    merge_id SERIAL PRIMARY KEY,
    operation VARCHAR(50) DEFAULT 'merge_cards',
    from_card_ids JSONB NOT NULL,
    to_card_id INT NOT NULL REFERENCES cards(card_id),
    affected_ste_ids JSONB NOT NULL,
    moderator_id INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    comment TEXT
);

CREATE INDEX IF NOT EXISTS idx_merge_logs_to_card ON card_merge_logs(to_card_id);
CREATE INDEX IF NOT EXISTS idx_merge_logs_created ON card_merge_logs(created_at);

-- =====================================================
-- Функция автообновления updated_at
-- =====================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Триггеры для автообновления
DROP TRIGGER IF EXISTS update_cards_updated_at ON cards;
CREATE TRIGGER update_cards_updated_at
    BEFORE UPDATE ON cards
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- =====================================================
-- Функция для вычисления хэша значимых характеристик
-- =====================================================
CREATE OR REPLACE FUNCTION calculate_significant_features_hash(
    p_card_id INT
) RETURNS VARCHAR(64) AS $$
DECLARE
    v_hash VARCHAR(64);
    v_features TEXT;
BEGIN
    -- Собираем отсортированный список значимых характеристик
    SELECT string_agg(feature_name || '=' || COALESCE(feature_value, ''), '|' ORDER BY feature_name)
    INTO v_features
    FROM card_significant_features
    WHERE card_id = p_card_id;
    
    -- Вычисляем MD5 хэш
    v_hash := MD5(COALESCE(v_features, ''));
    RETURN v_hash;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- Функция пересоздания карточек при изменении значимых характеристик
-- =====================================================
CREATE OR REPLACE FUNCTION recreate_cards_by_category(
    p_category_id INT
) RETURNS TABLE(
    old_card_id INT,
    new_card_id INT,
    ste_count INT
) AS $$
DECLARE
    v_ste RECORD;
    v_card_id INT;
    v_hash VARCHAR(64);
    v_features_hash VARCHAR(64);
    v_significant_features TEXT[];
BEGIN
    -- Получаем список значимых характеристик для категории (из шаблонов)
    SELECT array_agg(feature_name ORDER BY feature_name)
    INTO v_significant_features
    FROM category_feature_templates
    WHERE category_id = p_category_id
      AND is_recommended_significant = TRUE;
    
    -- Если нет шаблонов, используем все уникальные характеристики из СТЕ категории
    IF v_significant_features IS NULL OR array_length(v_significant_features, 1) = 0 THEN
        SELECT array_agg(DISTINCT key ORDER BY key)
        INTO v_significant_features
        FROM ste s
        JOIN cards c ON s.card_id = c.card_id
        WHERE c.category_id = p_category_id
          AND c.is_active = TRUE
          AND s.attributes IS NOT NULL;
    END IF;
    
    -- Деактивируем все старые карточки категории
    UPDATE cards SET is_active = FALSE WHERE category_id = p_category_id AND is_active = TRUE;
    
    -- Группируем СТЕ по значениям значимых характеристик
    FOR v_ste IN 
        SELECT s.ste_id, s.name, s.attributes, s.card_id
        FROM ste s
        JOIN cards c ON s.card_id = c.card_id
        WHERE c.category_id = p_category_id
          AND s.attributes IS NOT NULL
    LOOP
        -- Вычисляем хэш для этой СТЕ на основе значимых характеристик
        v_hash := '';
        IF v_significant_features IS NOT NULL THEN
            SELECT string_agg(
                COALESCE(v_ste.attributes->>feature_name, ''), 
                '|' 
                ORDER BY feature_name
            )
            INTO v_hash
            FROM unnest(v_significant_features) AS feature_name;
            v_hash := MD5(COALESCE(v_hash, ''));
        END IF;
        
        -- Ищем или создаём карточку с таким хэшем
        SELECT card_id INTO v_card_id
        FROM cards
        WHERE category_id = p_category_id
          AND significant_features_hash = v_hash
          AND is_active = TRUE
        LIMIT 1;
        
        IF v_card_id IS NULL THEN
            -- Создаём новую карточку
            INSERT INTO cards (title, description, category_id, significant_features_hash, is_active)
            VALUES (
                v_ste.name,
                NULL,
                p_category_id,
                v_hash,
                TRUE
            )
            RETURNING card_id INTO v_card_id;
            
            -- Добавляем значимые характеристики в карточку
            IF v_significant_features IS NOT NULL THEN
                INSERT INTO card_significant_features (card_id, feature_name, feature_value, display_order)
                SELECT 
                    v_card_id,
                    feature_name,
                    v_ste.attributes->>feature_name,
                    row_number() OVER (ORDER BY feature_name)
                FROM unnest(v_significant_features) AS feature_name
                WHERE v_ste.attributes->>feature_name IS NOT NULL;
            END IF;
        END IF;
        
        -- Привязываем СТЕ к карточке
        UPDATE ste SET card_id = v_card_id WHERE ste_id = v_ste.ste_id;
        
        -- Возвращаем результат
        RETURN QUERY SELECT v_ste.card_id, v_card_id, 1;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- Тестовые данные
-- =====================================================

-- Категории
INSERT INTO categories (name, parent_id) VALUES 
    ('Электроника', NULL),
    ('Смартфоны', 1),
    ('Ноутбуки', 1),
    ('Аксессуары', 1),
    ('Бытовая техника', NULL),
    ('Холодильники', 5),
    ('Стиральные машины', 5)
ON CONFLICT DO NOTHING;

-- Шаблоны значимых характеристик для категории "Смартфоны"
INSERT INTO category_feature_templates (category_id, feature_name, is_recommended_significant, usage_count) VALUES 
    (2, 'Производитель', TRUE, 100),
    (2, 'Модель', TRUE, 100),
    (2, 'Объём памяти', TRUE, 95),
    (2, 'Оперативная память', TRUE, 80),
    (2, 'Цвет', FALSE, 50),
    (2, 'Продавец', FALSE, 30)
ON CONFLICT DO NOTHING;

-- =====================================================
-- Вывод информации о созданных таблицах
-- =====================================================
DO $$
BEGIN
    RAISE NOTICE '✅ База данных успешно инициализирована!';
    RAISE NOTICE '📊 Созданы таблицы: categories, cards, ste, card_significant_features, category_feature_templates, feature_change_logs, card_merge_logs';
    RAISE NOTICE '📝 Добавлены тестовые данные';
END $$;

