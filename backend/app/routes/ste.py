from flask import Blueprint, request, jsonify
from app import db
from app.models import STE, Card

ste_bp = Blueprint('ste', __name__)


@ste_bp.route('/ste', methods=['GET'])
def get_all_ste():
    """Получить все СТЕ"""
    card_id = request.args.get('card_id', type=int)
    unassigned = request.args.get('unassigned', 'false').lower() == 'true'
    
    query = STE.query
    
    if unassigned:
        query = query.filter(STE.card_id.is_(None))
    elif card_id:
        query = query.filter_by(card_id=card_id)
    
    stes = query.all()
    
    return jsonify({
        'success': True,
        'data': {
            'stes': [s.to_dict() for s in stes],
            'total_count': len(stes)
        }
    })


@ste_bp.route('/ste/<int:ste_id>', methods=['GET'])
def get_ste(ste_id):
    """Получить СТЕ по ID"""
    ste = STE.query.get(ste_id)
    if not ste:
        return jsonify({
            'success': False,
            'message': 'СТЕ не найдена'
        }), 404
    
    return jsonify({
        'success': True,
        'data': ste.to_dict()
    })


@ste_bp.route('/ste', methods=['POST'])
def create_ste():
    """Создать новую СТЕ"""
    data = request.get_json()
    
    if not data or not data.get('name'):
        return jsonify({
            'success': False,
            'message': 'Поле name обязательно'
        }), 400
    
    ste = STE(
        name=data['name'],
        card_id=data.get('card_id'),
        attributes=data.get('attributes', {})
    )
    
    db.session.add(ste)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'data': ste.to_dict(),
        'message': 'СТЕ успешно создана'
    }), 201


@ste_bp.route('/ste/<int:ste_id>', methods=['PUT'])
def update_ste(ste_id):
    """Обновить СТЕ"""
    ste = STE.query.get(ste_id)
    if not ste:
        return jsonify({
            'success': False,
            'message': 'СТЕ не найдена'
        }), 404
    
    data = request.get_json()
    
    if 'name' in data:
        ste.name = data['name']
    if 'card_id' in data:
        ste.card_id = data['card_id']
    if 'attributes' in data:
        ste.attributes = data['attributes']
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'data': ste.to_dict(),
        'message': 'СТЕ успешно обновлена'
    })


@ste_bp.route('/ste/<int:ste_id>/assign', methods=['POST'])
def assign_ste_to_card(ste_id):
    """Привязать СТЕ к карточке"""
    ste = STE.query.get(ste_id)
    if not ste:
        return jsonify({
            'success': False,
            'message': 'СТЕ не найдена'
        }), 404
    
    data = request.get_json()
    card_id = data.get('card_id')
    
    if card_id:
        card = Card.query.get(card_id)
        if not card:
            return jsonify({
                'success': False,
                'message': 'Карточка не найдена'
            }), 404
    
    old_card_id = ste.card_id
    ste.card_id = card_id
    db.session.commit()
    
    return jsonify({
        'success': True,
        'data': {
            'ste_id': ste.ste_id,
            'old_card_id': old_card_id,
            'new_card_id': card_id
        },
        'message': 'СТЕ успешно привязана' if card_id else 'СТЕ откреплена от карточки'
    })


@ste_bp.route('/ste/<int:ste_id>', methods=['DELETE'])
def delete_ste(ste_id):
    """Удалить СТЕ"""
    ste = STE.query.get(ste_id)
    if not ste:
        return jsonify({
            'success': False,
            'message': 'СТЕ не найдена'
        }), 404
    
    db.session.delete(ste)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'СТЕ успешно удалена'
    })


