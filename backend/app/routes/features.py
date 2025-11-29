from flask import Blueprint, request, jsonify
from app import db
from app.models import Card, CardSignificantFeature, CategoryFeatureTemplate, STE

features_bp = Blueprint('features', __name__)


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
            'features_hash': card.significant_features_hash
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

