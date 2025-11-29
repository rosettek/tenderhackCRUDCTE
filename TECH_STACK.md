# Технологический стек проекта

## Оглавление
1. [Обзор архитектуры](#обзор-архитектуры)
2. [Frontend](#frontend)
3. [Backend](#backend)
4. [База данных](#база-данных)
5. [Docker](#docker)
6. [Быстрый старт](#быстрый-старт)

---

## Обзор архитектуры

```
┌─────────────────────────────────────────────────────────────────┐
│                         FRONTEND                                │
│                    HTML + JavaScript                            │
│                   (Vanilla JS / Fetch API)                      │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ HTTP/REST API
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                         BACKEND                                 │
│                      Flask (Python)                             │
│              Flask-CORS, Flask-SQLAlchemy                       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ SQL (psycopg2)
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                       DATABASE                                  │
│                  PostgreSQL 15+ (Docker)                        │
└─────────────────────────────────────────────────────────────────┘
```

---

## Frontend

### Технологии
| Технология | Версия | Описание |
|------------|--------|----------|
| HTML5 | - | Разметка страниц |
| CSS3 | - | Стилизация |
| JavaScript | ES6+ | Логика клиента |
| Fetch API | - | HTTP-запросы к API |

### Структура файлов
```
frontend/
├── index.html          # Главная страница
├── frontend.html       # Интерфейс модератора
├── css/
│   └── styles.css      # Стили
└── js/
    ├── api.js          # Модуль работы с API
    ├── cards.js        # Логика карточек
    ├── features.js     # Логика характеристик
    └── merge.js        # Логика объединения
```

### Пример API-клиента (JavaScript)

```javascript
// js/api.js
const API_BASE_URL = 'http://localhost:5000/api';

class ApiClient {
    constructor(baseUrl) {
        this.baseUrl = baseUrl;
    }

    async request(endpoint, options = {}) {
        const url = `${this.baseUrl}${endpoint}`;
        const config = {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        };

        try {
            const response = await fetch(url, config);
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.message || 'API Error');
            }
            
            return data;
        } catch (error) {
            console.error('API Request failed:', error);
            throw error;
        }
    }

    // Характеристики
    async getCardFeatures(cardId, onlySignificant = false) {
        return this.request(`/cards/${cardId}/features?only_significant=${onlySignificant}`);
    }

    async markFeatureInsignificant(cardId, featureName, options = {}) {
        return this.request(`/cards/${cardId}/features/mark-insignificant`, {
            method: 'POST',
            body: JSON.stringify({
                feature_name: featureName,
                ...options
            })
        });
    }

    async markFeatureSignificant(cardId, featureName, options = {}) {
        return this.request(`/cards/${cardId}/features/mark-significant`, {
            method: 'POST',
            body: JSON.stringify({
                feature_name: featureName,
                ...options
            })
        });
    }

    async changeFeatureValue(cardId, featureName, oldValue, newValue, comment = '') {
        return this.request(`/cards/${cardId}/features/change-value`, {
            method: 'PATCH',
            body: JSON.stringify({
                feature_name: featureName,
                old_value: oldValue,
                new_value: newValue,
                comment
            })
        });
    }

    // Объединение карточек
    async mergeCards(fromCardIds, toCardId, options = {}) {
        return this.request('/cards/merge', {
            method: 'POST',
            body: JSON.stringify({
                from_card_ids: fromCardIds,
                to_card_id: toCardId,
                ...options
            })
        });
    }

    async getMergePreview(fromCardIds, toCardId) {
        const ids = fromCardIds.join(',');
        return this.request(`/cards/merge-preview?from_card_ids=${ids}&to_card_id=${toCardId}`);
    }
}

const api = new ApiClient(API_BASE_URL);
export default api;
```

---

## Backend

### Технологии
| Технология | Версия | Описание |
|------------|--------|----------|
| Python | 3.11+ | Язык программирования |
| Flask | 3.0+ | Web-фреймворк |
| Flask-CORS | 4.0+ | Поддержка CORS |
| Flask-SQLAlchemy | 3.1+ | ORM для работы с БД |
| psycopg2-binary | 2.9+ | PostgreSQL драйвер |
| python-dotenv | 1.0+ | Переменные окружения |

### Структура проекта
```
backend/
├── app/
│   ├── __init__.py         # Инициализация Flask приложения
│   ├── config.py           # Конфигурация
│   ├── models/
│   │   ├── __init__.py
│   │   ├── card.py         # Модель карточки
│   │   ├── ste.py          # Модель СТЕ
│   │   ├── feature.py      # Модель характеристик
│   │   └── logs.py         # Модели логов
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── cards.py        # API карточек
│   │   ├── features.py     # API характеристик
│   │   └── merge.py        # API объединения
│   ├── services/
│   │   ├── __init__.py
│   │   ├── card_service.py
│   │   ├── feature_service.py
│   │   └── merge_service.py
│   └── utils/
│       ├── __init__.py
│       └── logger.py       # Утилиты логирования
├── migrations/             # Миграции Alembic
├── tests/                  # Тесты
├── requirements.txt        # Зависимости
├── run.py                  # Точка входа
└── .env                    # Переменные окружения
```

### requirements.txt

```txt
# Web Framework
Flask==3.0.0
Flask-CORS==4.0.0
Flask-SQLAlchemy==3.1.1
Flask-Migrate==4.0.5

# Database
psycopg2-binary==2.9.9
SQLAlchemy==2.0.23

# Utils
python-dotenv==1.0.0
marshmallow==3.20.1

# Development
pytest==7.4.3
pytest-flask==1.3.0
black==23.11.0
flake8==6.1.0
```

### Пример Flask приложения

```python
# app/__init__.py
from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from .config import Config

db = SQLAlchemy()
migrate = Migrate()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Инициализация расширений
    db.init_app(app)
    migrate.init_app(app, db)
    CORS(app)
    
    # Регистрация blueprints
    from .routes.cards import cards_bp
    from .routes.features import features_bp
    from .routes.merge import merge_bp
    
    app.register_blueprint(cards_bp, url_prefix='/api')
    app.register_blueprint(features_bp, url_prefix='/api')
    app.register_blueprint(merge_bp, url_prefix='/api')
    
    return app
```

```python
# app/config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key')
    
    # PostgreSQL
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 
        'postgresql://postgres:postgres@localhost:5432/tenderhack')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = os.environ.get('SQL_ECHO', 'false').lower() == 'true'
```

```python
# app/models/feature.py
from app import db
from datetime import datetime

class CardFeature(db.Model):
    __tablename__ = 'card_features'
    
    feature_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    card_id = db.Column(db.Integer, db.ForeignKey('cards.card_id', ondelete='CASCADE'), nullable=False)
    feature_name = db.Column(db.String(255), nullable=False)
    feature_value = db.Column(db.String(1000))
    is_significant = db.Column(db.Boolean, default=True)
    significance_weight = db.Column(db.Float, default=1.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'feature_id': self.feature_id,
            'card_id': self.card_id,
            'feature_name': self.feature_name,
            'feature_value': self.feature_value,
            'is_significant': self.is_significant,
            'significance_weight': self.significance_weight
        }
```

```python
# app/routes/features.py
from flask import Blueprint, request, jsonify
from app import db
from app.models.feature import CardFeature
from app.models.logs import FeatureChangeLog

features_bp = Blueprint('features', __name__)

@features_bp.route('/cards/<int:card_id>/features', methods=['GET'])
def get_card_features(card_id):
    only_significant = request.args.get('only_significant', 'false').lower() == 'true'
    
    query = CardFeature.query.filter_by(card_id=card_id)
    if only_significant:
        query = query.filter_by(is_significant=True)
    
    features = query.all()
    
    return jsonify({
        'success': True,
        'data': {
            'card_id': card_id,
            'features': [f.to_dict() for f in features],
            'total_count': len(features),
            'significant_count': sum(1 for f in features if f.is_significant)
        }
    })

@features_bp.route('/cards/<int:card_id>/features/mark-insignificant', methods=['POST'])
def mark_feature_insignificant(card_id):
    data = request.get_json()
    feature_name = data.get('feature_name')
    
    feature = CardFeature.query.filter_by(
        card_id=card_id, 
        feature_name=feature_name
    ).first()
    
    if not feature:
        return jsonify({'success': False, 'message': 'Характеристика не найдена'}), 404
    
    # Обновляем характеристику
    feature.is_significant = False
    
    # Логируем операцию
    log = FeatureChangeLog(
        operation='mark_insignificant',
        card_id=card_id,
        ste_id=data.get('ste_id'),
        feature_name=feature_name,
        became_insignificant=True,
        moderator_id=1,  # TODO: получить из сессии
        comment=data.get('comment')
    )
    
    db.session.add(log)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'data': {
            'feature_name': feature_name,
            'is_significant': False,
            'became_insignificant': True,
            'log_id': log.log_id
        },
        'message': 'Характеристика успешно помечена как незначимая'
    })
```

---

## База данных

### Технологии
| Технология | Версия | Описание |
|------------|--------|----------|
| PostgreSQL | 15+ | Реляционная СУБД |
| Docker | 24+ | Контейнеризация |

### Схема базы данных

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────────────┐
│    categories   │     │      cards      │     │       card_features     │
├─────────────────┤     ├─────────────────┤     ├─────────────────────────┤
│ category_id PK  │◄────│ category_id FK  │     │ feature_id PK           │
│ name            │     │ card_id PK      │◄────│ card_id FK              │
│ parent_id FK    │     │ title           │     │ feature_name            │
└─────────────────┘     │ description     │     │ feature_value           │
                        │ created_at      │     │ is_significant          │
                        │ updated_at      │     │ significance_weight     │
                        │ is_active       │     └─────────────────────────┘
                        └─────────────────┘
                                │
                                │
                        ┌───────▼─────────┐
                        │       ste       │
                        ├─────────────────┤
                        │ ste_id PK       │
                        │ card_id FK      │
                        │ name            │
                        │ attributes JSON │
                        │ created_at      │
                        └─────────────────┘

┌───────────────────────────┐     ┌─────────────────────────────┐
│   feature_change_logs     │     │      card_merge_logs        │
├───────────────────────────┤     ├─────────────────────────────┤
│ log_id PK                 │     │ merge_id PK                 │
│ operation ENUM            │     │ operation                   │
│ ste_id FK                 │     │ from_card_ids JSON          │
│ card_id FK                │     │ to_card_id FK               │
│ category_id FK            │     │ affected_ste_ids JSON       │
│ feature_name              │     │ moderator_id                │
│ old_value                 │     │ created_at                  │
│ new_value                 │     │ comment                     │
│ became_significant        │     └─────────────────────────────┘
│ became_insignificant      │
│ moderator_id              │
│ created_at                │
│ comment                   │
└───────────────────────────┘
```

---

## Docker

### docker-compose.yml

```yaml
version: '3.8'

services:
  # PostgreSQL Database
  postgres:
    image: postgres:15-alpine
    container_name: tenderhack_postgres
    restart: unless-stopped
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-postgres}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-postgres}
      POSTGRES_DB: ${POSTGRES_DB:-tenderhack}
      PGDATA: /var/lib/postgresql/data/pgdata
    ports:
      - "${POSTGRES_PORT:-5432}:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql:ro
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-postgres} -d ${POSTGRES_DB:-tenderhack}"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - tenderhack_network

  # pgAdmin (опционально, для управления БД)
  pgadmin:
    image: dpage/pgadmin4:latest
    container_name: tenderhack_pgadmin
    restart: unless-stopped
    environment:
      PGADMIN_DEFAULT_EMAIL: ${PGADMIN_EMAIL:-admin@admin.com}
      PGADMIN_DEFAULT_PASSWORD: ${PGADMIN_PASSWORD:-admin}
      PGADMIN_CONFIG_SERVER_MODE: 'False'
    ports:
      - "${PGADMIN_PORT:-5050}:80"
    volumes:
      - pgadmin_data:/var/lib/pgadmin
    depends_on:
      postgres:
        condition: service_healthy
    networks:
      - tenderhack_network

  # Flask Backend (опционально)
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: tenderhack_backend
    restart: unless-stopped
    environment:
      DATABASE_URL: postgresql://${POSTGRES_USER:-postgres}:${POSTGRES_PASSWORD:-postgres}@postgres:5432/${POSTGRES_DB:-tenderhack}
      FLASK_ENV: ${FLASK_ENV:-development}
      SECRET_KEY: ${SECRET_KEY:-your-secret-key}
    ports:
      - "${FLASK_PORT:-5000}:5000"
    volumes:
      - ./backend:/app
    depends_on:
      postgres:
        condition: service_healthy
    networks:
      - tenderhack_network

volumes:
  postgres_data:
    driver: local
  pgadmin_data:
    driver: local

networks:
  tenderhack_network:
    driver: bridge
```

### init.sql — Скрипт инициализации БД

```sql
-- Создание таблиц при первом запуске

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
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- СТЕ (Стандартные товарные единицы)
CREATE TABLE IF NOT EXISTS ste (
    ste_id SERIAL PRIMARY KEY,
    card_id INT REFERENCES cards(card_id) ON DELETE SET NULL,
    name VARCHAR(500) NOT NULL,
    attributes JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Характеристики карточек
CREATE TABLE IF NOT EXISTS card_features (
    feature_id SERIAL PRIMARY KEY,
    card_id INT NOT NULL REFERENCES cards(card_id) ON DELETE CASCADE,
    feature_name VARCHAR(255) NOT NULL,
    feature_value VARCHAR(1000),
    is_significant BOOLEAN DEFAULT TRUE,
    significance_weight FLOAT DEFAULT 1.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_card_features_card_id ON card_features(card_id);
CREATE INDEX IF NOT EXISTS idx_card_features_significant ON card_features(card_id, is_significant);
CREATE INDEX IF NOT EXISTS idx_card_features_name ON card_features(feature_name);

-- Значимость характеристик по категориям
CREATE TABLE IF NOT EXISTS category_feature_significance (
    id SERIAL PRIMARY KEY,
    category_id INT NOT NULL REFERENCES categories(category_id) ON DELETE CASCADE,
    feature_name VARCHAR(255) NOT NULL,
    is_significant BOOLEAN DEFAULT TRUE,
    updated_by INT,
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

-- Функция автообновления updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Триггеры для автообновления
CREATE TRIGGER update_cards_updated_at
    BEFORE UPDATE ON cards
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_card_features_updated_at
    BEFORE UPDATE ON card_features
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Тестовые данные (опционально)
INSERT INTO categories (name) VALUES 
    ('Электроника'),
    ('Смартфоны'),
    ('Ноутбуки')
ON CONFLICT DO NOTHING;
```

### Dockerfile для Backend

```dockerfile
# backend/Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Копирование и установка Python зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование исходного кода
COPY . .

# Переменные окружения
ENV FLASK_APP=run.py
ENV FLASK_ENV=development
ENV PYTHONUNBUFFERED=1

EXPOSE 5000

# Запуск приложения
CMD ["flask", "run", "--host=0.0.0.0"]
```

### .env файл

```env
# PostgreSQL
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=tenderhack
POSTGRES_PORT=5432

# pgAdmin
PGADMIN_EMAIL=admin@admin.com
PGADMIN_PASSWORD=admin
PGADMIN_PORT=5050

# Flask
FLASK_ENV=development
FLASK_PORT=5000
SECRET_KEY=your-super-secret-key-change-in-production

# Database URL для Flask
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/tenderhack
```

---

## Быстрый старт

### 1. Клонирование и настройка

```bash
# Клонируем репозиторий
git clone <repository-url>
cd tenderhackCRUDCTE

# Копируем пример .env файла
cp .env.example .env

# Редактируем переменные окружения (при необходимости)
nano .env
```

### 2. Запуск PostgreSQL в Docker

```bash
# Запуск только PostgreSQL
docker-compose up -d postgres

# Проверка статуса
docker-compose ps

# Просмотр логов
docker-compose logs -f postgres
```

### 3. Подключение к БД

```bash
# Через docker exec
docker exec -it tenderhack_postgres psql -U postgres -d tenderhack

# Или через psql (если установлен локально)
psql -h localhost -p 5432 -U postgres -d tenderhack
```

### 4. Запуск всех сервисов

```bash
# Запуск всех контейнеров
docker-compose up -d

# Проверка статуса
docker-compose ps

# Остановка
docker-compose down

# Остановка с удалением данных
docker-compose down -v
```

### 5. Запуск Backend локально (для разработки)

```bash
# Создаём виртуальное окружение
cd backend
python -m venv venv

# Активация (Windows)
.\venv\Scripts\activate

# Активация (Linux/Mac)
source venv/bin/activate

# Установка зависимостей
pip install -r requirements.txt

# Инициализация миграций
flask db init
flask db migrate -m "Initial migration"
flask db upgrade

# Запуск сервера
flask run
```

### 6. Проверка работоспособности

```bash
# Проверка PostgreSQL
docker exec tenderhack_postgres pg_isready -U postgres

# Проверка API
curl http://localhost:5000/api/cards/1/features

# Открыть pgAdmin
# http://localhost:5050
# Email: admin@admin.com
# Password: admin
```

---

## Полезные команды

### Docker

```bash
# Просмотр логов
docker-compose logs -f

# Перезапуск сервиса
docker-compose restart postgres

# Вход в контейнер
docker exec -it tenderhack_postgres bash

# Бэкап базы данных
docker exec tenderhack_postgres pg_dump -U postgres tenderhack > backup.sql

# Восстановление из бэкапа
docker exec -i tenderhack_postgres psql -U postgres tenderhack < backup.sql
```

### PostgreSQL

```sql
-- Список таблиц
\dt

-- Описание таблицы
\d card_features

-- Просмотр данных
SELECT * FROM cards LIMIT 10;

-- Проверка индексов
\di
```

### Flask

```bash
# Создание миграции
flask db migrate -m "Add new column"

# Применение миграций
flask db upgrade

# Откат миграции
flask db downgrade

# Запуск тестов
pytest

# Форматирование кода
black app/
```

---

## Контакты и поддержка

При возникновении проблем:
1. Проверьте логи: `docker-compose logs`
2. Убедитесь, что все порты свободны
3. Проверьте переменные окружения в `.env`

