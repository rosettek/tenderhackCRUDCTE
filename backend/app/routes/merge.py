from flask import Blueprint, request, jsonify
from app import db
from app.models import Card, STE, CardSignificantFeature, CardMergeLog

merge_bp = Blueprint('merge', __name__)


@merge_bp.route('/cards/merge-preview', methods=['GET'])
def merge_preview():
    """Предпросмотр объединения карточек"""
    from_card_ids_str = request.args.get('from_card_ids', '')
    to_card_id = request.args.get('to_card_id', type=int)
    
    if not from_card_ids_str:
        return jsonify({
            'success': False,
            'message': 'Параметр from_card_ids обязателен'
        }), 400
    
    try:
        from_card_ids = [int(x.strip()) for x in from_card_ids_str.split(',')]
    except ValueError:
        return jsonify({
            'success': False,
            'message': 'Неверный формат from_card_ids'
        }), 400
    
    # Получаем карточки для объединения
    cards_to_merge = Card.query.filter(Card.card_id.in_(from_card_ids)).all()
    
    if len(cards_to_merge) != len(from_card_ids):
        return jsonify({
            'success': False,
            'message': 'Одна или несколько карточек не найдены'
        }), 404
    
    # Получаем целевую карточку
    target_card = None
    if to_card_id:
        target_card = Card.query.get(to_card_id)
        if not target_card:
            return jsonify({
                'success': False,
                'message': 'Целевая карточка не найдена'
            }), 404
    
    # Проверяем, что все карточки из одной категории
    categories = set(c.category_id for c in cards_to_merge)
    if target_card:
        categories.add(target_card.category_id)
    
    if len(categories) > 1 and None not in categories:
        return jsonify({
            'success': False,
            'message': 'Карточки принадлежат разным категориям'
        }), 409
    
    # Собираем информацию о карточках
    cards_info = []
    total_ste_count = 0
    all_features = {}
    
    for card in cards_to_merge:
        ste_count = STE.query.filter_by(card_id=card.card_id).count()
        total_ste_count += ste_count
        cards_info.append({
            'card_id': card.card_id,
            'title': card.title,
            'ste_count': ste_count
        })
        
        # Собираем характеристики
        for feature in card.significant_features:
            if feature.feature_name not in all_features:
                all_features[feature.feature_name] = {
                    'values': set(),
                    'is_significant': True  # Все features в significant_features являются значимыми
                }
            all_features[feature.feature_name]['values'].add(feature.feature_value)
    
    # Находим конфликты (разные значения для одной характеристики)
    feature_conflicts = []
    for name, data in all_features.items():
        if len(data['values']) > 1:
            feature_conflicts.append({
                'feature_name': name,
                'values': list(data['values'])
            })
    
    # Формируем предложения по значимости
    significant_features = [name for name, data in all_features.items() if data['is_significant']]
    insignificant_features = []  # Все features в significant_features являются значимыми
    
    preview_data = {
        'total_ste_count': total_ste_count,
        'cards_to_merge': cards_info,
        'feature_conflicts': feature_conflicts,
        'suggested_features': {
            'significant': significant_features,
            'insignificant': insignificant_features
        }
    }
    
    if target_card:
        target_ste_count = STE.query.filter_by(card_id=target_card.card_id).count()
        preview_data['target_card'] = {
            'card_id': target_card.card_id,
            'title': target_card.title,
            'current_ste_count': target_ste_count
        }
        preview_data['total_ste_count'] += target_ste_count
    
    return jsonify({
        'success': True,
        'data': {
            'preview': preview_data
        }
    })


@merge_bp.route('/cards/merge', methods=['POST'])
def merge_cards():
    """Объединить карточки"""
    data = request.get_json()
    
    from_card_ids = data.get('from_card_ids', [])
    to_card_id = data.get('to_card_id')
    create_new_card = data.get('create_new_card', False)
    new_card_title = data.get('new_card_title')
    recalculate_features = data.get('recalculate_features', True)
    
    if not from_card_ids:
        return jsonify({
            'success': False,
            'message': 'Массив from_card_ids не может быть пустым'
        }), 400
    
    # Получаем исходные карточки
    source_cards = Card.query.filter(Card.card_id.in_(from_card_ids)).all()
    
    if len(source_cards) != len(from_card_ids):
        return jsonify({
            'success': False,
            'message': 'Одна или несколько карточек не найдены'
        }), 404
    
    # Определяем целевую карточку
    target_card = None
    
    if create_new_card:
        if not new_card_title:
            return jsonify({
                'success': False,
                'message': 'Для создания новой карточки требуется new_card_title'
            }), 400
        
        # Берём категорию из первой исходной карточки
        category_id = source_cards[0].category_id
        
        target_card = Card(
            title=new_card_title,
            category_id=category_id
        )
        db.session.add(target_card)
        db.session.flush()  # Чтобы получить card_id
    else:
        if not to_card_id:
            return jsonify({
                'success': False,
                'message': 'Требуется to_card_id или create_new_card=true'
            }), 400
        
        target_card = Card.query.get(to_card_id)
        if not target_card:
            return jsonify({
                'success': False,
                'message': 'Целевая карточка не найдена'
            }), 404
    
    # Проверяем категории
    categories = set(c.category_id for c in source_cards)
    categories.add(target_card.category_id)
    categories.discard(None)
    
    if len(categories) > 1:
        return jsonify({
            'success': False,
            'message': 'Карточки принадлежат разным категориям'
        }), 409
    
    # Переносим СТЕ
    affected_stes = []
    for card in source_cards:
        stes = STE.query.filter_by(card_id=card.card_id).all()
        for ste in stes:
            affected_stes.append({
                'ste_id': ste.ste_id,
                'old_card_id': ste.card_id,
                'new_card_id': target_card.card_id
            })
            ste.card_id = target_card.card_id
    
    # Пересчитываем характеристики если нужно
    merged_features = {'significant': [], 'recalculated': recalculate_features}
    
    if recalculate_features:
        # Собираем все характеристики из исходных карточек
        all_features = {}
        for card in source_cards:
            for feature in card.significant_features:
                key = feature.feature_name
                if key not in all_features:
                    all_features[key] = {
                        'value': feature.feature_value,
                        'display_order': feature.display_order
                    }
        
        # Добавляем характеристики к целевой карточке (если их там нет)
        existing_features = {f.feature_name for f in target_card.significant_features}
        
        for name, data in all_features.items():
            if name not in existing_features:
                new_feature = CardSignificantFeature(
                    card_id=target_card.card_id,
                    feature_name=name,
                    feature_value=data['value'],
                    display_order=data.get('display_order', 0)
                )
                db.session.add(new_feature)
            
            merged_features['significant'].append(name)
    
    # Деактивируем исходные карточки
    deactivated_cards = []
    for card in source_cards:
        if card.card_id != target_card.card_id:
            card.is_active = False
            deactivated_cards.append(card.card_id)
    
    # Логируем операцию
    log = CardMergeLog(
        operation='merge_cards',
        from_card_ids=from_card_ids,
        to_card_id=target_card.card_id,
        affected_ste_ids=[s['ste_id'] for s in affected_stes],
        moderator_id=data.get('moderator_id', 1),
        comment=data.get('comment')
    )
    db.session.add(log)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'data': {
            'merge_id': log.merge_id,
            'operation': 'merge_cards',
            'to_card_id': target_card.card_id,
            'from_card_ids': from_card_ids,
            'affected_ste': affected_stes,
            'merged_features': merged_features,
            'deactivated_cards': deactivated_cards
        },
        'message': 'Карточки успешно объединены'
    })


@merge_bp.route('/cards/<int:card_id>/merge-history', methods=['GET'])
def get_merge_history(card_id):
    """Получить историю объединений для карточки"""
    card = Card.query.get(card_id)
    if not card:
        return jsonify({
            'success': False,
            'message': 'Карточка не найдена'
        }), 404
    
    # Находим все объединения, где эта карточка была целевой
    merge_logs = CardMergeLog.query.filter_by(to_card_id=card_id).order_by(
        CardMergeLog.created_at.desc()
    ).all()
    
    history = []
    for log in merge_logs:
        history.append({
            'merge_id': log.merge_id,
            'operation': log.operation,
            'from_card_ids': log.from_card_ids,
            'affected_ste_count': len(log.affected_ste_ids) if log.affected_ste_ids else 0,
            'moderator_id': log.moderator_id,
            'created_at': log.created_at.isoformat() if log.created_at else None,
            'comment': log.comment
        })
    
    return jsonify({
        'success': True,
        'data': {
            'card_id': card_id,
            'merge_history': history
        }
    })

