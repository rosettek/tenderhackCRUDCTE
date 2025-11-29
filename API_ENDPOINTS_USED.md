# API Endpoints, используемые во frontend.html

## Базовый URL
```
http://localhost:5000/api
```

## Endpoints

### Карточки (Cards)

#### GET /cards ✅ РЕАЛИЗОВАНО
**Описание:** Получить список всех карточек  
**Использование:** `apiRequest('/cards')`  
**Метод:** GET  
**Параметры:** нет

#### GET /cards/{cardId}
**Описание:** Получить детальную информацию о карточке  
**Использование:** `apiRequest(`/cards/${cardId}`)`  
**Метод:** GET  
**Параметры:** 
- `cardId` (int) - ID карточки

#### POST /cards
**Описание:** Создать новую карточку  
**Использование:** `apiRequest('/cards', 'POST', { title, description })`  
**Метод:** POST  
**Тело запроса:**
```json
{
  "title": "string",
  "description": "string"
}
```

#### PUT /cards/{cardId}
**Описание:** Обновить карточку  
**Использование:** `apiRequest(`/cards/${cardId}`, 'PUT', { title, description })`  
**Метод:** PUT  
**Параметры:**
- `cardId` (int) - ID карточки  
**Тело запроса:**
```json
{
  "title": "string",
  "description": "string"
}
```

#### DELETE /cards/{cardId}
**Описание:** Удалить карточку  
**Использование:** `apiRequest(`/cards/${cardId}`, 'DELETE')`  
**Метод:** DELETE  
**Параметры:**
- `cardId` (int) - ID карточки

#### POST /cards/redistribute
**Описание:** Перераспределить СТЕ по карточкам  
**Использование:** `apiRequest('/cards/redistribute', 'POST', { significant_features })`  
**Метод:** POST  
**Тело запроса:**
```json
{
  "significant_features": ["string"]
}
```

#### GET /cards/merge-preview
**Описание:** Получить предпросмотр объединения карточек  
**Использование:** `apiRequest(`/cards/merge-preview?from_card_ids=${fromCardIds.join(',')}&to_card_id=${fromCardIds[0]}`)`  
**Метод:** GET  
**Query параметры:**
- `from_card_ids` (string) - список ID карточек через запятую
- `to_card_id` (int) - ID целевой карточки

#### POST /cards/merge
**Описание:** Объединить карточки  
**Использование:** `apiRequest('/cards/merge', 'POST', { from_card_ids, to_card_id, create_new_card, new_card_title, recalculate_features, comment })`  
**Метод:** POST  
**Тело запроса:**
```json
{
  "from_card_ids": [1, 2, 3],
  "to_card_id": 1,
  "create_new_card": false,
  "new_card_title": "string",
  "recalculate_features": true,
  "comment": "string"
}
```

#### GET /cards/{cardId}/merge-history
**Описание:** Получить историю объединений карточки  
**Использование:** `apiRequest(`/cards/${cardId}/merge-history`)`  
**Метод:** GET  
**Параметры:**
- `cardId` (int) - ID карточки

### Характеристики карточек (Features)

#### GET /cards/{cardId}/features
**Описание:** Получить список характеристик карточки  
**Использование:** `apiRequest(`/cards/${cardId}/features`)`  
**Метод:** GET  
**Параметры:**
- `cardId` (int) - ID карточки

#### POST /cards/{cardId}/features
**Описание:** Добавить характеристику к карточке  
**Использование:** `apiRequest(`/cards/${cardId}/features`, 'POST', { feature_name, feature_value, is_significant })`  
**Метод:** POST  
**Параметры:**
- `cardId` (int) - ID карточки  
**Тело запроса:**
```json
{
  "feature_name": "string",
  "feature_value": "string",
  "is_significant": true
}
```

#### POST /cards/{cardId}/features/mark-significant
**Описание:** Пометить характеристику как значимую  
**Использование:** `apiRequest(`/cards/${cardId}/features/mark-significant`, 'POST', { feature_name, trigger_redistribution })`  
**Метод:** POST  
**Параметры:**
- `cardId` (int) - ID карточки  
**Тело запроса:**
```json
{
  "feature_name": "string",
  "trigger_redistribution": true
}
```

#### POST /cards/{cardId}/features/mark-insignificant
**Описание:** Пометить характеристику как незначимую  
**Использование:** `apiRequest(`/cards/${cardId}/features/mark-insignificant`, 'POST', { feature_name, trigger_redistribution })`  
**Метод:** POST  
**Параметры:**
- `cardId` (int) - ID карточки  
**Тело запроса:**
```json
{
  "feature_name": "string",
  "trigger_redistribution": true
}
```

#### PATCH /cards/{cardId}/features/change-value
**Описание:** Изменить значение характеристики  
**Использование:** `apiRequest(`/cards/${cardId}/features/change-value`, 'PATCH', { feature_name, old_value, new_value, comment })`  
**Метод:** PATCH  
**Параметры:**
- `cardId` (int) - ID карточки  
**Тело запроса:**
```json
{
  "feature_name": "string",
  "old_value": "string",
  "new_value": "string",
  "comment": "string"
}
```

#### GET /cards/{cardId}/features/{featureName}/values
**Описание:** Получить все значения характеристики из СТЕ карточки  
**Использование:** `apiRequest(`/cards/${cardId}/features/${encodeURIComponent(featureName)}/values`)`  
**Метод:** GET  
**Параметры:**
- `cardId` (int) - ID карточки
- `featureName` (string) - название характеристики (URL encoded)

### СТЕ (Standard Trade Units)

#### GET /ste?unassigned=true ✅ РЕАЛИЗОВАНО
**Описание:** Получить список нераспределённых СТЕ  
**Использование:** `apiRequest('/ste?unassigned=true')`  
**Метод:** GET  
**Query параметры:**
- `unassigned` (boolean) - true для получения нераспределённых СТЕ

#### PUT /ste/{steId}
**Описание:** Обновить СТЕ  
**Использование:** `apiRequest(`/ste/${steId}`, 'PUT', { name, attributes })`  
**Метод:** PUT  
**Параметры:**
- `steId` (int) - ID СТЕ  
**Тело запроса:**
```json
{
  "name": "string",
  "attributes": {}
}
```

#### POST /ste/{steId}/assign
**Описание:** Привязать/отвязать СТЕ к карточке  
**Использование:** 
- Привязка: `apiRequest(`/ste/${steId}/assign`, 'POST', { card_id: parseInt(cardId) })`
- Отвязка: `apiRequest(`/ste/${steId}/assign`, 'POST', { card_id: null })`  
**Метод:** POST  
**Параметры:**
- `steId` (int) - ID СТЕ  
**Тело запроса:**
```json
{
  "card_id": 1  // или null для отвязки
}
```

#### GET /ste/attributes?card_id={cardId}
**Описание:** Получить список атрибутов из СТЕ карточки  
**Использование:** `apiRequest(`/ste/attributes?card_id=${cardId}`)`  
**Метод:** GET  
**Query параметры:**
- `card_id` (int) - ID карточки

## Итого

Всего используется **15 endpoints**:

### Карточки (8 endpoints):
1. GET /cards
2. GET /cards/{cardId}
3. POST /cards
4. PUT /cards/{cardId}
5. DELETE /cards/{cardId}
6. POST /cards/redistribute
7. GET /cards/merge-preview
8. POST /cards/merge
9. GET /cards/{cardId}/merge-history

### Характеристики (6 endpoints):
1. GET /cards/{cardId}/features
2. POST /cards/{cardId}/features
3. POST /cards/{cardId}/features/mark-significant
4. POST /cards/{cardId}/features/mark-insignificant
5. PATCH /cards/{cardId}/features/change-value
6. GET /cards/{cardId}/features/{featureName}/values

### СТЕ (4 endpoints):
1. GET /ste?unassigned=true
2. PUT /ste/{steId}
3. POST /ste/{steId}/assign
4. GET /ste/attributes?card_id={cardId}

