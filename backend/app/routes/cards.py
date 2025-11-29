from flask import Blueprint, request, jsonify
from app import db
from app.models import Card, Category

cards_bp = Blueprint('cards', __name__)


@cards_bp.route('/cards', methods=['GET'])
def get_cards():
    """Получить список всех карточек с СТЕ"""
    include_stes = request.args.get('include_stes', 'true').lower() == 'true'
    cards = Card.query.filter_by(is_active=True).all()
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
    
    # Получаем все СТЕ
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
    
    # Группируем СТЕ по значимым характеристикам
    groups = defaultdict(list)
    
    for ste in stes:
        if not ste.attributes:
            # СТЕ без атрибутов - в отдельную группу
            groups[('__no_attributes__',)].append(ste)
            continue
        
        # Создаём ключ группировки из значимых характеристик
        key_parts = []
        for feature in significant_features:
            value = ste.attributes.get(feature, '__missing__')
            key_parts.append(f"{feature}:{value}")
        
        group_key = tuple(sorted(key_parts))
        groups[group_key].append(ste)
    
    # Создаём/обновляем карточки для каждой группы
    created_cards = []
    updated_stes = []
    
    for group_key, group_stes in groups.items():
        if group_key == ('__no_attributes__',):
            card_title = "СТЕ без атрибутов"
        else:
            # Формируем название карточки из значений характеристик
            title_parts = [part.split(':')[1] for part in group_key if ':' in part]
            card_title = ' | '.join([p for p in title_parts if p != '__missing__'])
            if not card_title:
                card_title = "Группа СТЕ"
        
        # Создаём новую карточку
        new_card = Card(
            title=card_title,
            description=f"Автоматически создана при группировке по: {', '.join(significant_features)}",
            category_id=category_id
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
        
        # Добавляем характеристики к карточке
        for feature in significant_features:
            # Берём первое значение из группы
            sample_ste = group_stes[0]
            if sample_ste.attributes:
                value = sample_ste.attributes.get(feature)
                if value:
                    card_feature = CardSignificantFeature(
                        card_id=new_card.card_id,
                        feature_name=feature,
                        feature_value=str(value),
                        display_order=0
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

