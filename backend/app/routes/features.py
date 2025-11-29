from flask import Blueprint, request, jsonify
from app import db
from app.models import Card, CardSignificantFeature, CategoryFeatureTemplate, STE, FeatureChangeLog

features_bp = Blueprint('features', __name__)


@features_bp.route('/cards/<int:card_id>/features', methods=['GET'])
def get_card_features(card_id):
    """Получить список характеристик карточки из атрибутов СТЕ, входящих в карточку"""
    card = Card.query.get(card_id)
    if not card:
        return jsonify({
            'success': False,
            'message': 'Карточка не найдена'
        }), 404
    
    # Получаем все СТЕ, привязанные к этой карточке
    stes = STE.query.filter_by(card_id=card_id).all()
    
    # Собираем все уникальные характеристики из атрибутов СТЕ
    from collections import defaultdict
    features_map = defaultdict(set)  # feature_name -> set of values
    
    for ste in stes:
        if ste.attributes:
            for feature_name, value in ste.attributes.items():
                if value is not None:
                    features_map[feature_name].add(str(value))
    
    # Получаем список значимых характеристик из базы
    significant_features_db = card.significant_features.all()
    significant_feature_names = {f.feature_name for f in significant_features_db}
    
    # Формируем список всех характеристик
    features_list = []
    for feature_name in sorted(features_map.keys()):
        values = list(features_map[feature_name])
        # Берем первое значение как основное (или можно взять самое частое)
        feature_value = values[0] if values else None
        
        # Проверяем, является ли характеристика значимой
        is_significant = feature_name in significant_feature_names
        
        # Если характеристика значимая, берем значение из базы, если оно там есть
        if is_significant:
            sig_feature = next((f for f in significant_features_db if f.feature_name == feature_name), None)
            if sig_feature and sig_feature.feature_value:
                feature_value = sig_feature.feature_value
        
        features_list.append({
            'feature_name': feature_name,
            'feature_value': feature_value,
            'is_significant': is_significant,
            'display_order': next((f.display_order for f in significant_features_db if f.feature_name == feature_name), 0),
            'all_values': sorted(values),  # Все возможные значения для этой характеристики
            'values_count': len(values)
        })
    
    # Сортируем: сначала значимые (по display_order), потом остальные
    features_list.sort(key=lambda x: (not x['is_significant'], x['display_order'], x['feature_name']))
    
    return jsonify({
        'success': True,
        'data': {
            'card_id': card_id,
            'features': features_list,
            'significant_features': [f.to_dict() for f in significant_features_db],  # Оставляем для обратной совместимости
            'significant_features_list': card.significant_features_list or []
        }
    })


@features_bp.route('/cards/<int:card_id>/significant-features', methods=['GET'])
def get_significant_features(card_id):
    """Получить список значимых характеристик карточки"""
    card = Card.query.get(card_id)
    if not card:
        return jsonify({
            'success': False,
            'message': 'Карточка не найдена'
        }), 404
    
    features = card.significant_features.all()
    
    return jsonify({
        'success': True,
        'data': {
            'card_id': card_id,
            'significant_features': [f.to_dict() for f in features],
            'significant_features_list': card.significant_features_list or []
        }
    })


@features_bp.route('/cards/<int:card_id>/significant-features/add', methods=['POST'])
def add_significant_feature(card_id):
    """Добавить характеристику в список значимых для карточки"""
    card = Card.query.get(card_id)
    if not card:
        return jsonify({
            'success': False,
            'message': 'Карточка не найдена'
        }), 404
    
    data = request.get_json()
    if not data or not data.get('feature_name'):
        return jsonify({
            'success': False,
            'message': 'Поле feature_name обязательно'
        }), 400
    
    feature_name = data['feature_name']
    feature_value = data.get('feature_value')
    display_order = data.get('display_order', 0)
    
    # Проверяем, не существует ли уже такая характеристика
    existing = CardSignificantFeature.query.filter_by(
        card_id=card_id,
        feature_name=feature_name
    ).first()
    
    if existing:
        return jsonify({
            'success': False,
            'message': f'Характеристика {feature_name} уже добавлена'
        }), 400
    
    # Создаём новую значимую характеристику
    feature = CardSignificantFeature(
        card_id=card_id,
        feature_name=feature_name,
        feature_value=feature_value,
        display_order=display_order
    )
    
    db.session.add(feature)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'data': feature.to_dict(),
        'message': 'Характеристика успешно добавлена'
    }), 201


@features_bp.route('/cards/<int:card_id>/significant-features/remove', methods=['POST'])
def remove_significant_feature(card_id):
    """Убрать характеристику из списка значимых для карточки"""
    card = Card.query.get(card_id)
    if not card:
        return jsonify({
            'success': False,
            'message': 'Карточка не найдена'
        }), 404
    
    data = request.get_json()
    if not data or not data.get('feature_name'):
        return jsonify({
            'success': False,
            'message': 'Поле feature_name обязательно'
        }), 400
    
    feature_name = data['feature_name']
    
    # Находим и удаляем характеристику
    feature = CardSignificantFeature.query.filter_by(
        card_id=card_id,
        feature_name=feature_name
    ).first()
    
    if not feature:
        return jsonify({
            'success': False,
            'message': f'Характеристика {feature_name} не найдена'
        }), 404
    
    db.session.delete(feature)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': f'Характеристика {feature_name} успешно удалена'
    })


@features_bp.route('/cards/<int:card_id>/features/mark-significant', methods=['POST'])
def mark_feature_significant(card_id):
    """Пометить характеристику как значимую (добавить в список значимых)"""
    card = Card.query.get(card_id)
    if not card:
        return jsonify({
            'success': False,
            'message': 'Карточка не найдена'
        }), 404
    
    data = request.get_json() or {}
    feature_name = data.get('feature_name')
    
    if not feature_name:
        return jsonify({
            'success': False,
            'message': 'Поле feature_name обязательно'
        }), 400
    
    # Проверяем, не существует ли уже такая характеристика
    existing = CardSignificantFeature.query.filter_by(
        card_id=card_id,
        feature_name=feature_name
    ).first()
    
    if existing:
        return jsonify({
            'success': False,
            'message': f'Характеристика {feature_name} уже является значимой'
        }), 400
    
    # Получаем значение характеристики из СТЕ карточки (берем первое значение)
    stes = STE.query.filter_by(card_id=card_id).all()
    feature_value = None
    for ste in stes:
        if ste.attributes and feature_name in ste.attributes:
            feature_value = str(ste.attributes[feature_name])
            break
    
    # Определяем display_order (следующий после последнего)
    last_order = db.session.query(db.func.max(CardSignificantFeature.display_order)).filter_by(
        card_id=card_id
    ).scalar() or -1
    
    # Создаём новую значимую характеристику
    feature = CardSignificantFeature(
        card_id=card_id,
        feature_name=feature_name,
        feature_value=feature_value,
        display_order=last_order + 1
    )
    
    db.session.add(feature)
    
    # Обновляем список значимых характеристик в карточке
    significant_features_names = sorted([f.feature_name for f in card.significant_features.all()])
    card.significant_features_list = significant_features_names
    
    # Логируем операцию
    log = FeatureChangeLog(
        operation='mark_significant',
        card_id=card_id,
        category_id=card.category_id,
        feature_name=feature_name,
        new_value=feature_value,
        became_significant=True,
        moderator_id=data.get('moderator_id', 1),
        comment=data.get('comment')
    )
    db.session.add(log)
    db.session.commit()
    
    # Автоматически перераспределяем карточки категории, если указано
    redistribution_result = None
    if card.category_id and data.get('trigger_redistribution', True):
        from app.services.card_recreation import recreate_cards_for_category
        try:
            redistribution_result = recreate_cards_for_category(
                category_id=card.category_id,
                significant_features=None,  # Используем текущие значимые характеристики из карточек
                moderator_id=data.get('moderator_id', 1),
                comment=f'Автоматическое перераспределение после пометки характеристики "{feature_name}" как значимой'
            )
        except Exception as e:
            # Логируем ошибку, но не прерываем выполнение
            print(f"Ошибка при перераспределении карточек: {e}")
    
    return jsonify({
        'success': True,
        'data': {
            'feature': feature.to_dict(),
            'log_id': log.log_id,
            'needs_redistribution': True,
            'is_significant': True,
            'significant_features_list': significant_features_names,
            'redistribution': redistribution_result
        },
        'message': 'Характеристика успешно помечена как значимая' + (' и карточки перераспределены' if redistribution_result else '')
    })


@features_bp.route('/cards/<int:card_id>/features/mark-insignificant', methods=['POST'])
def mark_feature_insignificant(card_id):
    """Пометить характеристику как незначимую (убрать из списка значимых)"""
    card = Card.query.get(card_id)
    if not card:
        return jsonify({
            'success': False,
            'message': 'Карточка не найдена'
        }), 404
    
    data = request.get_json() or {}
    feature_name = data.get('feature_name')
    
    if not feature_name:
        return jsonify({
            'success': False,
            'message': 'Поле feature_name обязательно'
        }), 400
    
    # Находим характеристику в значимых
    feature = CardSignificantFeature.query.filter_by(
        card_id=card_id,
        feature_name=feature_name
    ).first()
    
    if not feature:
        return jsonify({
            'success': False,
            'message': f'Характеристика {feature_name} не найдена в списке значимых'
        }), 404
    
    # Сохраняем старое значение для лога
    old_value = feature.feature_value
    
    # Удаляем характеристику из значимых
    db.session.delete(feature)
    
    # Обновляем список значимых характеристик в карточке
    # Нужно перезагрузить карточку, чтобы получить актуальный список
    db.session.flush()  # Применяем удаление
    card = Card.query.get(card_id)  # Перезагружаем карточку
    significant_features_names = sorted([f.feature_name for f in card.significant_features.all()])
    card.significant_features_list = significant_features_names
    
    # Логируем операцию
    log = FeatureChangeLog(
        operation='mark_insignificant',
        card_id=card_id,
        category_id=card.category_id,
        feature_name=feature_name,
        old_value=old_value,
        became_insignificant=True,
        moderator_id=data.get('moderator_id', 1),
        comment=data.get('comment')
    )
    db.session.add(log)
    db.session.commit()
    
    # Автоматически перераспределяем карточки категории, если указано
    redistribution_result = None
    if card.category_id and data.get('trigger_redistribution', True):
        from app.services.card_recreation import recreate_cards_for_category
        try:
            redistribution_result = recreate_cards_for_category(
                category_id=card.category_id,
                significant_features=None,  # Используем текущие значимые характеристики из карточек
                moderator_id=data.get('moderator_id', 1),
                comment=f'Автоматическое перераспределение после пометки характеристики "{feature_name}" как незначимой'
            )
        except Exception as e:
            # Логируем ошибку, но не прерываем выполнение
            print(f"Ошибка при перераспределении карточек: {e}")
    
    return jsonify({
        'success': True,
        'data': {
            'feature_name': feature_name,
            'is_significant': False,
            'log_id': log.log_id,
            'needs_redistribution': True,
            'significant_features_list': significant_features_names,
            'redistribution': redistribution_result
        },
        'message': 'Характеристика успешно помечена как незначимая' + (' и карточки перераспределены' if redistribution_result else '')
    })


@features_bp.route('/cards/<int:card_id>/features/<feature_name>/values', methods=['GET'])
def get_feature_values(card_id, feature_name):
    """Получить все возможные значения характеристики в карточке (для выпадающего меню)"""
    card = Card.query.get(card_id)
    if not card:
        return jsonify({
            'success': False,
            'message': 'Карточка не найдена'
        }), 404
    
    # Получаем все СТЕ карточки
    stes = STE.query.filter_by(card_id=card_id).all()
    
    # Собираем все уникальные значения характеристики
    values_set = set()
    for ste in stes:
        if ste.attributes and feature_name in ste.attributes:
            value = ste.attributes[feature_name]
            if value is not None:
                values_set.add(str(value))
    
    # Проверяем, является ли характеристика значимой
    sig_feature = CardSignificantFeature.query.filter_by(
        card_id=card_id,
        feature_name=feature_name
    ).first()
    
    return jsonify({
        'success': True,
        'data': {
            'card_id': card_id,
            'feature_name': feature_name,
            'is_significant': sig_feature is not None,
            'current_value': sig_feature.feature_value if sig_feature else None,
            'all_values': sorted(list(values_set)),
            'values_count': len(values_set)
        }
    })


@features_bp.route('/cards/<int:card_id>/available-features', methods=['GET'])
def get_available_features(card_id):
    """Получить список всех доступных характеристик для добавления в значимые"""
    card = Card.query.get(card_id)
    if not card:
        return jsonify({
            'success': False,
            'message': 'Карточка не найдена'
        }), 404
    
    # Получаем текущие значимые характеристики
    current_significant = [f.feature_name for f in card.significant_features.all()]
    
    # Получаем все уникальные атрибуты из СТЕ категории
    from collections import defaultdict
    attributes_map = defaultdict(set)
    
    if card.category_id:
        # Получаем все СТЕ категории
        stes = STE.query.join(Card).filter(Card.category_id == card.category_id).all()
        for ste in stes:
            if ste.attributes:
                for key, value in ste.attributes.items():
                    attributes_map[key].add(str(value))
    
    # Получаем шаблоны из категории
    templates = []
    if card.category_id:
        templates = CategoryFeatureTemplate.query.filter_by(
            category_id=card.category_id
        ).all()
    
    # Формируем список доступных характеристик
    available_features = []
    for feature_name in sorted(attributes_map.keys()):
        is_currently_significant = feature_name in current_significant
        template = next((t for t in templates if t.feature_name == feature_name), None)
        
        available_features.append({
            'feature_name': feature_name,
            'usage_count': len(attributes_map[feature_name]),
            'is_recommended': template.is_recommended_significant if template else False,
            'is_currently_significant': is_currently_significant,
            'sample_values': sorted(list(attributes_map[feature_name]))[:5]  # Первые 5 значений
        })
    
    return jsonify({
        'success': True,
        'data': {
            'card_id': card_id,
            'current_significant_features': current_significant,
            'available_features': available_features
        }
    })

