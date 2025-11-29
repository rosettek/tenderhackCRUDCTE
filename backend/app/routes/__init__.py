# Routes package
from flask import Blueprint, request, jsonify
from app.services.card_recreation import recreate_cards_for_category

api_bp = Blueprint('api', __name__)

@api_bp.route('/categories/<int:category_id>/recreate-cards', methods=['POST'])
def recreate_cards_by_category(category_id):
    data = request.get_json() or {}
    significant_features = data.get('significant_features')
    comment = data.get('comment')
    moderator_id = data.get('moderator_id', 1)
    result = recreate_cards_for_category(category_id, significant_features, moderator_id, comment)
    if 'error' in result:
        return jsonify({'success': False, 'message': result['error'], 'data': result}), 400
    return jsonify({'success': True, 'message': 'Карточки категории успешно пересозданы', 'data': result})

