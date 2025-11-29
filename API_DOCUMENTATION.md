# API Документация: Управление карточками и характеристиками

## Оглавление
1. [Структуры базы данных](#структуры-базы-данных)
2. [API Endpoints](#api-endpoints)
   - [Работа с характеристиками](#работа-с-характеристиками)
   - [Объединение карточек](#объединение-карточек)
3. [Логирование операций](#логирование-операций)

---

## Структуры базы данных

### Таблица `cards` — Карточки товаров

| Поле | Тип | Описание |
|------|-----|----------|
| `card_id` | INT, PRIMARY KEY, AUTO_INCREMENT | Уникальный идентификатор карточки |
| `title` | VARCHAR(500) | Название карточки |
| `description` | TEXT | Описание карточки |
| `category_id` | INT, FOREIGN KEY | Идентификатор категории |
| `significant_features_hash` | VARCHAR(64) | MD5 хэш значимых характеристик (для группировки) |
| `created_at` | TIMESTAMP | Дата создания |
| `updated_at` | TIMESTAMP | Дата последнего обновления |
| `is_active` | BOOLEAN, DEFAULT TRUE | Активна ли карточка |

```sql
CREATE TABLE cards (
    card_id INT PRIMARY KEY AUTO_INCREMENT,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    category_id INT,
    significant_features_hash VARCHAR(64),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (category_id) REFERENCES categories(category_id),
    INDEX idx_cards_sig_hash (significant_features_hash) WHERE is_active = TRUE
);
```

**Важно:** Карточки группируются по одинаковым значениям значимых характеристик. При изменении списка значимых характеристик карточки пересоздаются автоматически.

---

### Таблица `ste` — Стандартные товарные единицы (СТЕ)

| Поле | Тип | Описание |
|------|-----|----------|
| `ste_id` | INT, PRIMARY KEY, AUTO_INCREMENT | Уникальный идентификатор СТЕ |
| `card_id` | INT, FOREIGN KEY | Привязка к карточке |
| `name` | VARCHAR(500) | Название СТЕ |
| `attributes` | JSONB | Все атрибуты СТЕ в формате `{"feature_name": "value", ...}` |
| `created_at` | TIMESTAMP | Дата создания |

```sql
CREATE TABLE ste (
    ste_id INT PRIMARY KEY AUTO_INCREMENT,
    card_id INT,
    name VARCHAR(500) NOT NULL,
    attributes JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (card_id) REFERENCES cards(card_id) ON DELETE SET NULL,
    INDEX idx_ste_card_id (card_id),
    INDEX idx_ste_attributes USING GIN(attributes)
);
```

**Важно:** Все характеристики СТЕ хранятся в поле `attributes` как JSON объект. При пересоздании карточек СТЕ автоматически перегруппировываются по значениям значимых характеристик.

---

### Таблица `card_significant_features` — Значимые характеристики карточки

**Ключевая таблица!** Список значимых характеристик определяет группировку СТЕ в карточки. При изменении этого списка карточки автоматически пересоздаются.

| Поле | Тип | Описание |
|------|-----|----------|
| `id` | INT, PRIMARY KEY, AUTO_INCREMENT | Уникальный идентификатор |
| `card_id` | INT, FOREIGN KEY | Привязка к карточке |
| `feature_name` | VARCHAR(255) | Название значимой характеристики |
| `feature_value` | VARCHAR(1000) | Значение характеристики (вычисляется из СТЕ) |
| `display_order` | INT, DEFAULT 0 | Порядок отображения |
| `created_at` | TIMESTAMP | Дата создания |

```sql
CREATE TABLE card_significant_features (
    id INT PRIMARY KEY AUTO_INCREMENT,
    card_id INT NOT NULL,
    feature_name VARCHAR(255) NOT NULL,
    feature_value VARCHAR(1000),
    display_order INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (card_id) REFERENCES cards(card_id) ON DELETE CASCADE,
    UNIQUE KEY unique_card_feature (card_id, feature_name),
    INDEX idx_card_sig_features_card (card_id),
    INDEX idx_card_sig_features_name (feature_name)
);
```

**Логика работы:**
- СТЕ с **одинаковыми значениями** всех значимых характеристик → объединяются в одну карточку
- При добавлении/удалении значимой характеристики → все карточки категории пересоздаются
- Значения значимых характеристик берутся из `attributes` СТЕ

---

### Таблица `category_feature_templates` — Шаблоны значимых характеристик по категориям

**Справочная таблица** для подсказок и рекомендаций. Не влияет напрямую на группировку, но используется при автоматическом пересоздании карточек.

| Поле | Тип | Описание |
|------|-----|----------|
| `id` | INT, PRIMARY KEY, AUTO_INCREMENT | Уникальный идентификатор |
| `category_id` | INT, FOREIGN KEY | Идентификатор категории |
| `feature_name` | VARCHAR(255) | Название характеристики |
| `is_recommended_significant` | BOOLEAN, DEFAULT TRUE | Рекомендуется ли как значимая |
| `usage_count` | INT, DEFAULT 0 | Количество использований в категории |
| `updated_at` | TIMESTAMP | Дата обновления |

```sql
CREATE TABLE category_feature_templates (
    id INT PRIMARY KEY AUTO_INCREMENT,
    category_id INT NOT NULL,
    feature_name VARCHAR(255) NOT NULL,
    is_recommended_significant BOOLEAN DEFAULT TRUE,
    usage_count INT DEFAULT 0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (category_id) REFERENCES categories(category_id) ON DELETE CASCADE,
    UNIQUE KEY unique_category_feature (category_id, feature_name)
);
```

---

### Таблица `feature_change_logs` — Логи изменений характеристик

| Поле | Тип | Описание |
|------|-----|----------|
| `log_id` | INT, PRIMARY KEY, AUTO_INCREMENT | Уникальный идентификатор лога |
| `operation` | ENUM | Тип операции |
| `ste_id` | INT, NULLABLE | ID СТЕ (если применимо) |
| `card_id` | INT | ID карточки |
| `category_id` | INT, NULLABLE | ID категории |
| `feature_name` | VARCHAR(255) | Название характеристики |
| `old_value` | VARCHAR(1000), NULLABLE | Старое значение |
| `new_value` | VARCHAR(1000), NULLABLE | Новое значение |
| `became_significant` | BOOLEAN, NULLABLE | Стала значимой |
| `became_insignificant` | BOOLEAN, NULLABLE | Стала незначимой |
| `moderator_id` | INT | ID модератора |
| `created_at` | TIMESTAMP | Дата операции |
| `comment` | TEXT, NULLABLE | Комментарий модератора |

```sql
CREATE TABLE feature_change_s (
    log_id INT PRIMARY KEY AUTO_INCREMENT,
    operation ENUM(
        'mark_significant',
        'mark_insignificant', 
        'change_value',
        'add_feature',
        'remove_feature'
    ) NOT NULL,
    ste_id INT NULL,
    card_id INT NOT NULL,
    category_id INT NULL,
    feature_name VARCHAR(255) NOT NULL,
    old_value VARCHAR(1000) NULL,
    new_value VARCHAR(1000) NULL,
    became_significant BOOLEAN NULL,
    became_insignificant BOOLEAN NULL,
    moderator_id INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    comment TEXT NULL,
    FOREIGN KEY (card_id) REFERENCES cards(card_id) ON DELETE CASCADE,
    FOREIGN KEY (ste_id) REFERENCES ste(ste_id) ON DELETE SET NULL,
    INDEX idx_card_logs (card_id),
    INDEX idx_operation (operation),
    INDEX idx_created_at (created_at)
);
```

---

### Таблица `card_merge_logs` — Логи объединения карточек

| Поле | Тип | Описание |
|------|-----|----------|
| `merge_id` | INT, PRIMARY KEY, AUTO_INCREMENT | Уникальный идентификатор операции |
| `operation` | VARCHAR(50) | Тип операции (merge_cards) |
| `from_card_ids` | JSON | Массив ID исходных карточек |
| `to_card_id` | INT | ID целевой карточки |
| `affected_ste_ids` | JSON | Массив ID перемещённых СТЕ |
| `moderator_id` | INT | ID модератора |
| `created_at` | TIMESTAMP | Дата операции |
| `comment` | TEXT, NULLABLE | Комментарий модератора |

```sql
CREATE TABLE card_merge_logs (
    merge_id INT PRIMARY KEY AUTO_INCREMENT,
    operation VARCHAR(50) DEFAULT 'merge_cards',
    from_card_ids JSON NOT NULL,
    to_card_id INT NOT NULL,
    affected_ste_ids JSON NOT NULL,
    moderator_id INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    comment TEXT NULL,
    FOREIGN KEY (to_card_id) REFERENCES cards(card_id),
    INDEX idx_to_card (to_card_id),
    INDEX idx_created_at (created_at)
);
```

---

## Логика работы с значимыми характеристиками

### Принцип группировки СТЕ в карточки

1. **Каждая карточка** имеет список **значимых характеристик** (таблица `card_significant_features`)
2. **СТЕ группируются** в карточки по **одинаковым значениям** всех значимых характеристик
3. **При изменении** списка значимых характеристик → все карточки категории **пересоздаются автоматически**

### Пример работы

**Исходное состояние:**
- Значимые характеристики: `["Производитель", "Модель"]`
- СТЕ 1: `{"Производитель": "Samsung", "Модель": "S21", "Цвет": "Black"}`
- СТЕ 2: `{"Производитель": "Samsung", "Модель": "S21", "Цвет": "White"}`
- СТЕ 3: `{"Производитель": "Samsung", "Модель": "S21", "Цвет": "Black", "Память": "128GB"}`
- **Результат:** Все 3 СТЕ в одной карточке (значения `Производитель` и `Модель` совпадают)

**После добавления "Память" в значимые:**
- Значимые характеристики: `["Производитель", "Модель", "Память"]`
- СТЕ 1 и 2: `{"Производитель": "Samsung", "Модель": "S21", "Память": null}` → Карточка A
- СТЕ 3: `{"Производитель": "Samsung", "Модель": "S21", "Память": "128GB"}` → Карточка B
- **Результат:** СТЕ перегруппированы в 2 карточки

---

## API Endpoints

### Работа с характеристиками

---

#### GET `/api/cards/{card_id}/significant-features`

**Описание:** Получить список значимых характеристик карточки. Эти характеристики определяют, какие СТЕ объединяются в эту карточку.

**Параметры пути:**
| Параметр | Тип | Описание |
|----------|-----|----------|
| `card_id` | INT | Идентификатор карточки |

**Успешный ответ (200 OK):**
```json
{
    "success": true,
    "data": {
        "card_id": 123,
        "significant_features": [
            {
                "id": 1,
                "feature_name": "Производитель",
                "feature_value": "Samsung",
                "display_order": 0
            },
            {
                "id": 2,
                "feature_name": "Модель",
                "feature_value": "Galaxy S21",
                "display_order": 1
            },
            {
                "id": 3,
                "feature_name": "Объём памяти",
                "feature_value": "128GB",
                "display_order": 2
            }
        ],
        "total_count": 3,
        "features_hash": "a1b2c3d4e5f6..."
    }
}
```

**Ошибки:**
- `404 Not Found` — Карточка не найдена

---

#### GET `/api/cards/{card_id}/ste-attributes`

**Описание:** Получить все характеристики из СТЕ, привязанных к карточке (все атрибуты из `attributes` JSON).

**Параметры пути:**
| Параметр | Тип | Описание |
|----------|-----|----------|
| `card_id` | INT | Идентификатор карточки |

**Успешный ответ (200 OK):**
```json
{
    "success": true,
    "data": {
        "card_id": 123,
        "all_features": {
            "Производитель": "Samsung",
            "Модель": "Galaxy S21",
            "Объём памяти": "128GB",
            "Цвет": ["Black", "White"],
            "Оперативная память": "8GB"
        },
        "ste_count": 2
    }
}
```

**Ошибки:**
- `404 Not Found` — Карточка не найдена

---

#### POST `/api/cards/{card_id}/significant-features/remove`

**Описание:** Убрать характеристику из списка значимых для карточки. **Важно:** Это вызовет пересоздание всех карточек в категории!

**Параметры пути:**
| Параметр | Тип | Описание |
|----------|-----|----------|
| `card_id` | INT | Идентификатор карточки |

**Тело запроса:**
```json
{
    "feature_name": "Цвет",
    "recreate_cards": true,  // автоматически пересоздать карточки категории
    "comment": "Цвет не влияет на группировку товаров"
}
```

**Успешный ответ (200 OK):**
```json
{
    "success": true,
    "data": {
        "feature_name": "Цвет",
        "removed_from_card": 123,
        "log_id": 789,
        "cards_recreated": true,
        "recreated_cards_count": 15,
        "affected_category_id": 2
    },
    "message": "Характеристика убрана из значимых. Карточки категории пересозданы."
}
```

**Ошибки:**
- `404 Not Found` — Карточка или характеристика не найдена
- `400 Bad Request` — Неверные параметры запроса

---

#### POST `/api/cards/{card_id}/significant-features/add`

**Описание:** Добавить характеристику в список значимых для карточки. **Важно:** Это вызовет пересоздание всех карточек в категории!

**Параметры пути:**
| Параметр | Тип | Описание |
|----------|-----|----------|
| `card_id` | INT | Идентификатор карточки |

**Тело запроса:**
```json
{
    "feature_name": "Объём памяти",
    "display_order": 2,
    "recreate_cards": true,  // автоматически пересоздать карточки категории
    "comment": "Объём памяти критичен для группировки"
}
```

**Успешный ответ (200 OK):**
```json
{
    "success": true,
    "data": {
        "feature_name": "Объём памяти",
        "added_to_card": 123,
        "display_order": 2,
        "log_id": 790,
        "cards_recreated": true,
        "recreated_cards_count": 15,
        "affected_category_id": 2
    },
    "message": "Характеристика добавлена в значимые. Карточки категории пересозданы."
}
```

**Ошибки:**
- `404 Not Found` — Карточка не найдена
- `400 Bad Request` — Неверные параметры запроса
- `409 Conflict` — Характеристика уже в списке значимых

---

#### PATCH `/api/ste/{ste_id}/attributes`

**Описание:** Изменить значение характеристики в СТЕ. Если изменяется значимая характеристика, это может вызвать пересоздание карточек.

**Параметры пути:**
| Параметр | Тип | Описание |
|----------|-----|----------|
| `ste_id` | INT | Идентификатор СТЕ |

**Тело запроса:**
```json
{
    "feature_name": "Производитель",
    "old_value": "Sumsung",      // для верификации
    "new_value": "Samsung",
    "recreate_cards": true,      // пересоздать карточки если это значимая характеристика
    "comment": "Исправлена опечатка в названии производителя"
}
```

**Успешный ответ (200 OK):**
```json
{
    "success": true,
    "data": {
        "ste_id": 456,
        "feature_name": "Производитель",
        "old_value": "Sumsung",
        "new_value": "Samsung",
        "is_significant": true,
        "cards_recreated": true,
        "new_card_id": 125,
        "log_id": 791
    },
    "message": "Значение характеристики успешно изменено. СТЕ перемещена в новую карточку."
}
```

**Ошибки:**
- `404 Not Found` — СТЕ не найдена
- `400 Bad Request` — Неверные параметры или старое значение не совпадает
- `409 Conflict` — Значение уже было изменено другим модератором

---

#### GET `/api/cards/{card_id}/available-features`

**Описание:** Получить список всех доступных характеристик для добавления в значимые (из атрибутов СТЕ категории и шаблонов).

**Параметры пути:**
| Параметр | Тип | Описание |
|----------|-----|----------|
| `card_id` | INT | Идентификатор карточки |

**Успешный ответ (200 OK):**
```json
{
    "success": true,
    "data": {
        "card_id": 123,
        "category_id": 5,
        "current_significant_features": ["Производитель", "Модель", "Объём памяти"],
        "available_features": [
            {
                "feature_name": "Гарантия",
                "usage_count": 150,
                "is_recommended": false,
                "is_currently_significant": false
            },
            {
                "feature_name": "Оперативная память",
                "usage_count": 89,
                "is_recommended": true,
                "is_currently_significant": false
            }
        ]
    }
}
```

---

#### POST `/api/categories/{category_id}/recreate-cards`

**Описание:** Пересоздать все карточки категории на основе текущих значимых характеристик. Используется после изменения списка значимых характеристик.

**Параметры пути:**
| Параметр | Тип | Описание |
|----------|-----|----------|
| `category_id` | INT | Идентификатор категории |

**Тело запроса (опционально):**
```json
{
    "significant_features": ["Производитель", "Модель", "Объём памяти"],  // если не указано, берутся из шаблонов
    "comment": "Пересоздание после изменения значимых характеристик"
}
```

**Успешный ответ (200 OK):**
```json
{
    "success": true,
    "data": {
        "category_id": 2,
        "old_cards_deactivated": 10,
        "new_cards_created": 15,
        "ste_reassigned": 45,
        "significant_features_used": ["Производитель", "Модель", "Объём памяти"],
        "redistribution_summary": [
            {
                "old_card_id": 101,
                "new_card_id": 201,
                "ste_count": 3
            },
            {
                "old_card_id": 102,
                "new_card_id": 202,
                "ste_count": 5
            }
        ]
    },
    "message": "Карточки категории успешно пересозданы"
}
```

**Ошибки:**
- `404 Not Found` — Категория не найдена
- `400 Bad Request` — Неверные параметры запроса

---

### Объединение карточек

---

#### POST `/api/cards/merge`

**Описание:** Объединить несколько карточек в одну.

**Тело запроса:**
```json
{
    "from_card_ids": [101, 102, 103],
    "to_card_id": 100,                  // или null для создания новой
    "create_new_card": false,
    "new_card_title": "Новая карточка", // только если create_new_card = true
    "recalculate_features": true,
    "comment": "Объединение дублирующихся карточек Samsung Galaxy S21"
}
```

**Успешный ответ (200 OK):**
```json
{
    "success": true,
    "data": {
        "merge_id": 50,
        "operation": "merge_cards",
        "to_card_id": 100,
        "from_card_ids": [101, 102, 103],
        "affected_ste": [
            {
                "ste_id": 201,
                "old_card_id": 101,
                "new_card_id": 100
            },
            {
                "ste_id": 202,
                "old_card_id": 102,
                "new_card_id": 100
            },
            {
                "ste_id": 203,
                "old_card_id": 103,
                "new_card_id": 100
            }
        ],
        "merged_features": {
            "significant": ["Производитель", "Модель", "Объём памяти"],
            "recalculated": true
        },
        "deactivated_cards": [101, 102, 103]
    },
    "message": "Карточки успешно объединены"
}
```

**Ошибки:**
- `404 Not Found` — Одна или несколько карточек не найдены
- `400 Bad Request` — Неверные параметры (например, пустой массив from_card_ids)
- `409 Conflict` — Карточки принадлежат разным категориям

---

#### GET `/api/cards/merge-preview`

**Описание:** Предпросмотр результата объединения карточек (без фактического выполнения).

**Query параметры:**
| Параметр | Тип | Описание |
|----------|-----|----------|
| `from_card_ids` | STRING | Список ID через запятую (101,102,103) |
| `to_card_id` | INT | ID целевой карточки |

**Успешный ответ (200 OK):**
```json
{
    "success": true,
    "data": {
        "preview": {
            "total_ste_count": 15,
            "cards_to_merge": [
                {
                    "card_id": 101,
                    "title": "Samsung Galaxy S21 128GB",
                    "ste_count": 5
                },
                {
                    "card_id": 102,
                    "title": "Samsung Galaxy S21 128 ГБ",
                    "ste_count": 7
                }
            ],
            "target_card": {
                "card_id": 100,
                "title": "Samsung Galaxy S21",
                "current_ste_count": 3
            },
            "feature_conflicts": [
                {
                    "feature_name": "Название",
                    "values": ["Samsung Galaxy S21 128GB", "Samsung Galaxy S21 128 ГБ"]
                }
            ],
            "suggested_features": {
                "significant": ["Производитель", "Модель", "Объём памяти"],
                "insignificant": ["Цвет", "Продавец"]
            }
        }
    }
}
```

---

#### GET `/api/cards/{card_id}/merge-history`

**Описание:** Получить историю объединений для карточки.

**Параметры пути:**
| Параметр | Тип | Описание |
|----------|-----|----------|
| `card_id` | INT | Идентификатор карточки |

**Успешный ответ (200 OK):**
```json
{
    "success": true,
    "data": {
        "card_id": 100,
        "merge_history": [
            {
                "merge_id": 50,
                "operation": "merge_cards",
                "from_card_ids": [101, 102],
                "affected_ste_count": 12,
                "moderator_id": 5,
                "moderator_name": "Иван Петров",
                "created_at": "2025-11-29T10:30:00Z",
                "comment": "Объединение дублей"
            }
        ]
    }
}
```

---

## Логирование операций

### Структура лога изменения характеристик

Каждая операция с характеристиками автоматически логируется:

```json
{
    "log_id": 789,
    "operation": "mark_insignificant",
    "ste_id": 456,
    "card_id": 123,
    "category_id": 5,
    "feature_name": "Цвет",
    "old_value": null,
    "new_value": null,
    "became_significant": false,
    "became_insignificant": true,
    "moderator_id": 10,
    "created_at": "2025-11-29T14:22:00Z",
    "comment": "Цвет не влияет на группировку"
}
```

### Структура лога объединения карточек

```json
{
    "merge_id": 50,
    "operation": "merge_cards",
    "from_card_ids": [101, 102, 103],
    "to_card_id": 100,
    "affected_ste_ids": [201, 202, 203, 204, 205],
    "moderator_id": 10,
    "created_at": "2025-11-29T14:25:00Z",
    "comment": "Объединение дублирующихся карточек"
}
```

---

## Использование данных для обучения ML

### Экспорт обучающего датасета

#### GET `/api/ml/training-data/features`

**Описание:** Экспорт данных об изменениях значимости характеристик для обучения модели.

**Query параметры:**
| Параметр | Тип | Описание |
|----------|-----|----------|
| `from_date` | DATE | Начальная дата |
| `to_date` | DATE | Конечная дата |
| `category_id` | INT | Фильтр по категории |

**Успешный ответ (200 OK):**
```json
{
    "success": true,
    "data": {
        "training_samples": [
            {
                "category_id": 5,
                "feature_name": "Цвет",
                "is_significant": false,
                "sample_count": 45,
                "confidence": 0.89
            },
            {
                "category_id": 5,
                "feature_name": "Объём памяти",
                "is_significant": true,
                "sample_count": 120,
                "confidence": 0.97
            }
        ],
        "total_samples": 2
    }
}
```

---

#### GET `/api/ml/training-data/merges`

**Описание:** Экспорт данных об объединениях карточек для обучения модели группировки.

**Query параметры:**
| Параметр | Тип | Описание |
|----------|-----|----------|
| `from_date` | DATE | Начальная дата |
| `to_date` | DATE | Конечная дата |
| `category_id` | INT | Фильтр по категории |

**Успешный ответ (200 OK):**
```json
{
    "success": true,
    "data": {
        "merge_samples": [
            {
                "merge_id": 50,
                "category_id": 5,
                "merged_card_features": {
                    "card_101": {"Производитель": "Samsung", "Модель": "Galaxy S21"},
                    "card_102": {"Производитель": "Samsung", "Модель": "Galaxy S21"}
                },
                "label": "should_merge",
                "created_at": "2025-11-29T14:25:00Z"
            }
        ],
        "total_samples": 1
    }
}
```

---

## Коды ошибок

| Код | Описание |
|-----|----------|
| `200` | Успешное выполнение |
| `201` | Ресурс успешно создан |
| `400` | Неверные параметры запроса |
| `401` | Не авторизован |
| `403` | Нет прав на выполнение операции |
| `404` | Ресурс не найден |
| `409` | Конфликт (например, конкурентное изменение) |
| `500` | Внутренняя ошибка сервера |

---

## Примеры использования

### Пример 1: Убрать характеристику из значимых (вызовет пересоздание карточек)

```bash
curl -X POST "https://api.example.com/api/cards/123/significant-features/remove" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "feature_name": "Цвет",
    "recreate_cards": true,
    "comment": "Цвет не влияет на группировку в этой категории"
  }'
```

### Пример 2: Объединить карточки

```bash
curl -X POST "https://api.example.com/api/cards/merge" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "from_card_ids": [101, 102],
    "to_card_id": 100,
    "recalculate_features": true,
    "comment": "Объединение дублей Samsung Galaxy S21"
  }'
```

### Пример 3: Изменить значение характеристики в СТЕ

```bash
curl -X PATCH "https://api.example.com/api/ste/456/attributes" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "feature_name": "Производитель",
    "old_value": "Sumsung",
    "new_value": "Samsung",
    "recreate_cards": true,
    "comment": "Исправление опечатки"
  }'
```

### Пример 4: Пересоздать карточки категории

```bash
curl -X POST "https://api.example.com/api/categories/2/recreate-cards" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "significant_features": ["Производитель", "Модель", "Объём памяти"],
    "comment": "Пересоздание после изменения значимых характеристик"
  }'
```

