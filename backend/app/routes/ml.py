from flask import Blueprint, request, jsonify
from datetime import datetime
from sqlalchemy import func
from app import db
from app.models import FeatureChangeLog, CardMergeLog, Card, CardSignificantFeature

ml_bp = Blueprint('ml', __name__)


@ml_bp.route('/ml/training-data/features', methods=['GET'])
def get_feature_training_data():
    """Экспорт данных об изменениях значимости для обучения ML"""
    from_date = request.args.get('from_date')
    to_date = request.args.get('to_date')
    category_id = request.args.get('category_id', type=int)
    
    query = db.session.query(
        FeatureChangeLog.category_id,
        FeatureChangeLog.feature_name,
        FeatureChangeLog.operation,
        func.count(FeatureChangeLog.log_id).label('sample_count')
    ).filter(
        FeatureChangeLog.operation.in_(['mark_significant', 'mark_insignificant'])
    )
    
    if from_date:
        try:
            from_dt = datetime.fromisoformat(from_date)
            query = query.filter(FeatureChangeLog.created_at >= from_dt)
        except ValueError:
            pass
    
    if to_date:
        try:
            to_dt = datetime.fromisoformat(to_date)
            query = query.filter(FeatureChangeLog.created_at <= to_dt)
        except ValueError:
            pass
    
    if category_id:
        query = query.filter(FeatureChangeLog.category_id == category_id)
    
    results = query.group_by(
        FeatureChangeLog.category_id,
        FeatureChangeLog.feature_name,
        FeatureChangeLog.operation
    ).all()
    
    # Агрегируем данные
    feature_data = {}
    for category_id, feature_name, operation, count in results:
        key = (category_id, feature_name)
        if key not in feature_data:
            feature_data[key] = {
                'category_id': category_id,
                'feature_name': feature_name,
                'significant_count': 0,
                'insignificant_count': 0
            }
        
        if operation == 'mark_significant':
            feature_data[key]['significant_count'] = count
        else:
            feature_data[key]['insignificant_count'] = count
    
    # Формируем результат с confidence
    training_samples = []
    for data in feature_data.values():
        total = data['significant_count'] + data['insignificant_count']
        is_significant = data['significant_count'] > data['insignificant_count']
        confidence = max(data['significant_count'], data['insignificant_count']) / total if total > 0 else 0
        
        training_samples.append({
            'category_id': data['category_id'],
            'feature_name': data['feature_name'],
            'is_significant': is_significant,
            'sample_count': total,
            'confidence': round(confidence, 2)
        })
    
    return jsonify({
        'success': True,
        'data': {
            'training_samples': training_samples,
            'total_samples': len(training_samples)
        }
    })


@ml_bp.route('/ml/training-data/merges', methods=['GET'])
def get_merge_training_data():
    """Экспорт данных об объединениях для обучения ML"""
    from_date = request.args.get('from_date')
    to_date = request.args.get('to_date')
    category_id = request.args.get('category_id', type=int)
    
    query = CardMergeLog.query
    
    if from_date:
        try:
            from_dt = datetime.fromisoformat(from_date)
            query = query.filter(CardMergeLog.created_at >= from_dt)
        except ValueError:
            pass
    
    if to_date:
        try:
            to_dt = datetime.fromisoformat(to_date)
            query = query.filter(CardMergeLog.created_at <= to_dt)
        except ValueError:
            pass
    
    merge_logs = query.order_by(CardMergeLog.created_at.desc()).all()
    
    merge_samples = []
    for log in merge_logs:
        # Получаем информацию о карточках
        target_card = Card.query.get(log.to_card_id)
        
        # Фильтруем по категории если указана
        if category_id and target_card and target_card.category_id != category_id:
            continue
        
        # Собираем характеристики объединённых карточек
        merged_card_features = {}
        
        # Характеристики исходных карточек (если они ещё существуют)
        for card_id in log.from_card_ids:
            card = Card.query.get(card_id)
            if card:
                features = {f.feature_name: f.feature_value for f in card.significant_features}
                merged_card_features[f'card_{card_id}'] = features
        
        merge_samples.append({
            'merge_id': log.merge_id,
            'category_id': target_card.category_id if target_card else None,
            'merged_card_features': merged_card_features,
            'label': 'should_merge',
            'created_at': log.created_at.isoformat() if log.created_at else None
        })
    
    return jsonify({
        'success': True,
        'data': {
            'merge_samples': merge_samples,
            'total_samples': len(merge_samples)
        }
    })

