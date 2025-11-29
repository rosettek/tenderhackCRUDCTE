from flask import Blueprint, request, jsonify
from app import db
from app.models import Card, Category

cards_bp = Blueprint('cards', __name__)


@cards_bp.route('/cards', methods=['GET'])
def get_cards():
    """Получить список всех карточек с СТЕ"""
    include_stes = request.args.get('include_stes', 'true').lower() == 'true'
    category_id = request.args.get('category_id', type=int)
    
    query = Card.query.filter_by(is_active=True)
    if category_id:
        query = query.filter_by(category_id=category_id)
    
    cards = query.all()
    return jsonify({
        'success': True,
        'data': {
            'cards': [c.to_dict(include_stes=include_stes) for c in cards],
            'total_count': len(cards)
        }
    })


@cards_bp.route('/cards/<int:card_id>', methods=['GET'])
def get_card(card_id):
    """Получить карточку по ID"""
    card = Card.query.get(card_id)
    if not card:
        return jsonify({
            'success': False,
            'message': 'Карточка не найдена'
        }), 404
    
    return jsonify({
        'success': True,
        'data': card.to_dict(include_significant_features=True, include_stes=True)
    })


@cards_bp.route('/cards', methods=['POST'])
def create_card():
    """Создать новую карточку"""
    data = request.get_json()
    
    if not data or not data.get('title'):
        return jsonify({
            'success': False,
            'message': 'Поле title обязательно'
        }), 400
    
    card = Card(
        title=data['title'],
        description=data.get('description'),
        category_id=data.get('category_id')
    )
    
    db.session.add(card)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'data': card.to_dict(),
        'message': 'Карточка успешно создана'
    }), 201


@cards_bp.route('/cards/<int:card_id>', methods=['PUT'])
def update_card(card_id):
    """Обновить карточку"""
    card = Card.query.get(card_id)
    if not card:
        return jsonify({
            'success': False,
            'message': 'Карточка не найдена'
        }), 404
    
    data = request.get_json()
    
    if not data:
        return jsonify({
            'success': False,
            'message': 'Тело запроса не может быть пустым'
        }), 400
    
    if 'title' in data:
        card.title = data['title']
    if 'description' in data:
        card.description = data['description']
    if 'category_id' in data:
        card.category_id = data['category_id']
    if 'is_active' in data:
        card.is_active = data['is_active']
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'data': card.to_dict(),
        'message': 'Карточка успешно обновлена'
    })


@cards_bp.route('/cards/<int:card_id>', methods=['DELETE'])
def delete_card(card_id):
    """Удалить карточку (деактивировать)"""
    card = Card.query.get(card_id)
    if not card:
        return jsonify({
            'success': False,
            'message': 'Карточка не найдена'
        }), 404
    
    card.is_active = False
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Карточка успешно удалена'
    })


@cards_bp.route('/cards/redistribute', methods=['POST'])
def redistribute_cards():
    """
    Перераспределить СТЕ по карточкам на основе значимых характеристик.
    
    Логика:
    - Значимые характеристики (is_significant=True): группируем СТЕ с одинаковыми значениями в одну карточку
    - Незначимые характеристики: создаём отдельную карточку для каждого уникального значения
    """
    data = request.get_json() or {}
    significant_features = data.get('significant_features', [])  # Список значимых характеристик
    category_id = data.get('category_id')
    
    from app.models import STE, CardSignificantFeature
    from collections import defaultdict
    
    # Получаем СТЕ (все или только для категории)
    if category_id:
        stes = STE.query.join(Card).filter(Card.category_id == category_id).all()
    else:
        stes = STE.query.all()
    
    if not significant_features:
        # Если не указаны значимые характеристики, возвращаем текущее состояние
        return jsonify({
            'success': True,
            'data': {
                'status': 'no_changes',
                'message': 'Не указаны значимые характеристики для группировки',
                'current_stats': {
                    'total_stes': len(stes),
                    'assigned_stes': len([s for s in stes if s.card_id]),
                    'unassigned_stes': len([s for s in stes if not s.card_id]),
                    'total_cards': Card.query.filter_by(is_active=True).count()
                }
            }
        })
    
    # Собираем все уникальные характеристики из всех СТЕ категории
    all_features_set = set()
    for ste in stes:
        if ste.attributes:
            all_features_set.update(ste.attributes.keys())
    
    # Определяем незначимые характеристики (все характеристики, кроме значимых)
    insignificant_features = sorted(list(all_features_set - set(significant_features)))
    
    # Группируем СТЕ по значимым И незначимым характеристикам
    # Значимые - группируют, незначимые - разбивают на отдельные карточки
    groups = defaultdict(list)
    
    for ste in stes:
        if not ste.attributes:
            # СТЕ без атрибутов - в отдельную группу
            groups[('__no_attributes__',)].append(ste)
            continue
        
        # Создаём ключ группировки:
        # 1. Сначала по значимым характеристикам (группируют)
        # 2. Потом по незначимым характеристикам (разбивают на отдельные карточки)
        key_parts = []
        
        # Добавляем значимые характеристики
        for feature in significant_features:
            value = ste.attributes.get(feature, '__missing__')
            key_parts.append(f"sig:{feature}:{value}")
        
        # Добавляем незначимые характеристики (каждое значение = отдельная карточка)
        for feature in insignificant_features:
            value = ste.attributes.get(feature, '__missing__')
            key_parts.append(f"insig:{feature}:{value}")
        
        group_key = tuple(sorted(key_parts))
        groups[group_key].append(ste)
    
    # Деактивируем старые карточки категории (если указана категория)
    if category_id:
        old_cards = Card.query.filter_by(category_id=category_id, is_active=True).all()
        for old_card in old_cards:
            old_card.is_active = False
    
    # Создаём/обновляем карточки для каждой группы
    created_cards = []
    updated_stes = []
    
    for group_key, group_stes in groups.items():
        if group_key == ('__no_attributes__',):
            card_title = "СТЕ без атрибутов"
        else:
            # Формируем название карточки только из значимых характеристик
            # (незначимые не показываем в названии, так как они разбивают на отдельные карточки)
            title_parts = []
            for part in group_key:
                if part.startswith('sig:'):
                    # Формат: sig:feature_name:value
                    parts = part.split(':', 2)
                    if len(parts) == 3 and parts[2] != '__missing__':
                        title_parts.append(parts[2])
            
            card_title = ' | '.join(title_parts) if title_parts else "Группа СТЕ"
        
        # Создаём новую карточку
        new_card = Card(
            title=card_title,
            description=f"Автоматически создана при группировке по: {', '.join(significant_features)}",
            category_id=category_id,
            significant_features_list=sorted(significant_features)  # Сохраняем список названий характеристик
        )
        db.session.add(new_card)
        db.session.flush()
        
        # Привязываем СТЕ к карточке
        for ste in group_stes:
            ste.card_id = new_card.card_id
            updated_stes.append({
                'ste_id': ste.ste_id,
                'new_card_id': new_card.card_id
            })
        
        # Добавляем значимые характеристики к карточке
        for idx, feature in enumerate(significant_features):
            # Для значимых характеристик берем значение из группы
            # (все СТЕ в группе должны иметь одинаковое значение значимых характеристик)
            sample_ste = group_stes[0]
            if sample_ste.attributes:
                value = sample_ste.attributes.get(feature)
                if value:
                    # Проверяем, не существует ли уже такая характеристика
                    existing = CardSignificantFeature.query.filter_by(
                        card_id=new_card.card_id,
                        feature_name=feature
                    ).first()
                    if not existing:
                        card_feature = CardSignificantFeature(
                            card_id=new_card.card_id,
                            feature_name=feature,
                            feature_value=str(value),  # Значение для группировки (все СТЕ в карточке имеют это значение)
                            display_order=idx
                        )
                        db.session.add(card_feature)
        
        created_cards.append({
            'card_id': new_card.card_id,
            'title': new_card.title,
            'ste_count': len(group_stes)
        })
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'data': {
            'status': 'completed',
            'created_cards': created_cards,
            'updated_stes_count': len(updated_stes),
            'groups_count': len(groups)
        },
        'message': f'Создано {len(created_cards)} карточек, распределено {len(updated_stes)} СТЕ'
    })


@cards_bp.route('/cards/<int:card_id>/stes', methods=['GET'])
def get_card_stes(card_id):
    """Получить список СТЕ карточки"""
    card = Card.query.get(card_id)
    if not card:
        return jsonify({
            'success': False,
            'message': 'Карточка не найдена'
        }), 404
    
    from app.models import STE
    stes = STE.query.filter_by(card_id=card_id).all()
    
    return jsonify({
        'success': True,
        'data': {
            'card_id': card_id,
            'stes': [s.to_dict() for s in stes],
            'total_count': len(stes)
        }
    })


@cards_bp.route('/ste/attributes', methods=['GET'])
def get_all_ste_attributes():
    """
    Получить все уникальные атрибуты из всех СТЕ.
    Возвращает список атрибутов с их возможными значениями.
    """
    from app.models import STE
    from collections import defaultdict
    
    card_id = request.args.get('card_id', type=int)
    
    # Получаем СТЕ (все или только для конкретной карточки)
    if card_id:
        stes = STE.query.filter_by(card_id=card_id).all()
    else:
        stes = STE.query.all()
    
    # Собираем все атрибуты и их значения
    attributes_map = defaultdict(set)
    
    for ste in stes:
        if ste.attributes:
            for key, value in ste.attributes.items():
                attributes_map[key].add(str(value))
    
    # Формируем результат
    attributes_list = []
    for attr_name, values in sorted(attributes_map.items()):
        attributes_list.append({
            'name': attr_name,
            'values': sorted(list(values)),
            'values_count': len(values)
        })
    
    return jsonify({
        'success': True,
        'data': {
            'attributes': attributes_list,
            'total_attributes': len(attributes_list),
            'total_stes_analyzed': len(stes)
        }
    })

