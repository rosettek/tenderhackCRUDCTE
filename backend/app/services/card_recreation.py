"""
Сервис пересоздания карточек при изменении значимых характеристик
"""
import hashlib
from typing import List, Dict, Optional, Tuple
from app import db
from app.models import Card, STE, CardSignificantFeature, CategoryFeatureTemplate, FeatureChangeLog


def calculate_features_hash(feature_names: List[str], ste_attributes: Dict) -> str:
    """Вычислить MD5 хэш значимых характеристик для СТЕ"""
    values = []
    for feature_name in sorted(feature_names):
        value = ste_attributes.get(feature_name, '') if ste_attributes else ''
        values.append(f"{feature_name}={value}")
    features_str = '|'.join(values)
    return hashlib.md5(features_str.encode()).hexdigest()


def get_significant_features_for_category(category_id: int, custom_features: Optional[List[str]] = None) -> List[str]:
    """Получить список значимых характеристик для категории"""
    if custom_features:
        return custom_features
    
    # Получаем из шаблонов
    templates = CategoryFeatureTemplate.query.filter_by(
        category_id=category_id,
        is_recommended_significant=True
    ).order_by(CategoryFeatureTemplate.usage_count.desc()).all()
    
    if templates:
        return [t.feature_name for t in templates]
    
    # Если нет шаблонов, собираем все уникальные характеристики из СТЕ категории
    from sqlalchemy import func
    stes = db.session.query(STE).join(Card).filter(
        Card.category_id == category_id,
        Card.is_active == True
    ).all()
    
    feature_names = set()
    for ste in stes:
        if ste.attributes:
            feature_names.update(ste.attributes.keys())
    
    return sorted(list(feature_names))


def recreate_cards_for_category(
    category_id: int,
    significant_features: Optional[List[str]] = None,
    moderator_id: int = 1,
    comment: Optional[str] = None
) -> Dict:
    """
    Пересоздать все карточки категории на основе значимых характеристик
    
    Returns:
        Dict с информацией о пересоздании:
        {
            'old_cards_deactivated': int,
            'new_cards_created': int,
            'ste_reassigned': int,
            'significant_features_used': List[str],
            'redistribution_summary': List[Dict]
        }
    """
    # Получаем список значимых характеристик
    sig_features = get_significant_features_for_category(category_id, significant_features)
    
    if not sig_features:
        return {
            'old_cards_deactivated': 0,
            'new_cards_created': 0,
            'ste_reassigned': 0,
            'significant_features_used': [],
            'redistribution_summary': [],
            'error': 'Нет значимых характеристик для категории'
        }
    
    # Деактивируем все старые карточки категории
    old_cards = Card.query.filter_by(category_id=category_id, is_active=True).all()
    old_card_ids = [c.card_id for c in old_cards]
    
    for card in old_cards:
        card.is_active = False
    
    # Получаем все СТЕ категории
    stes = db.session.query(STE).join(Card).filter(
        Card.category_id == category_id
    ).all()
    
    # Группируем СТЕ по хэшу значимых характеристик
    cards_by_hash: Dict[str, Card] = {}
    redistribution_summary = []
    ste_reassigned = 0
    
    for ste in stes:
        if not ste.attributes:
            continue
        
        # Вычисляем хэш для этой СТЕ
        features_hash = calculate_features_hash(sig_features, ste.attributes)
        
        # Ищем или создаём карточку с таким хэшем
        if features_hash not in cards_by_hash:
            # Создаём новую карточку
            new_card = Card(
                title=ste.name,
                description=None,
                category_id=category_id,
                significant_features_hash=features_hash,
                is_active=True
            )
            db.session.add(new_card)
            db.session.flush()  # Получаем card_id
            
            # Добавляем значимые характеристики в карточку
            for idx, feature_name in enumerate(sig_features):
                feature_value = ste.attributes.get(feature_name)
                if feature_value is not None:
                    sig_feature = CardSignificantFeature(
                        card_id=new_card.card_id,
                        feature_name=feature_name,
                        feature_value=str(feature_value),
                        display_order=idx
                    )
                    db.session.add(sig_feature)
            
            cards_by_hash[features_hash] = new_card
            
            # Логируем создание новой карточки
            redistribution_summary.append({
                'old_card_id': ste.card_id,
                'new_card_id': new_card.card_id,
                'ste_count': 0  # Будет обновлено ниже
            })
        
        # Привязываем СТЕ к карточке
        old_card_id = ste.card_id
        ste.card_id = cards_by_hash[features_hash].card_id
        ste_reassigned += 1
        
        # Обновляем счётчик СТЕ в summary
        for summary_item in redistribution_summary:
            if summary_item['new_card_id'] == ste.card_id:
                summary_item['ste_count'] += 1
                break
    
    # Логируем операцию (используем первую созданную карточку для card_id, если есть)
    if cards_by_hash:
        first_card_id = list(cards_by_hash.values())[0].card_id
        log = FeatureChangeLog(
            operation='recreate_cards',
            card_id=first_card_id,
            category_id=category_id,
            feature_name=','.join(sig_features),
            moderator_id=moderator_id,
            comment=comment or f'Пересоздание карточек категории. Значимые характеристики: {", ".join(sig_features)}'
        )
        db.session.add(log)
    
    db.session.commit()
    
    return {
        'old_cards_deactivated': len(old_card_ids),
        'new_cards_created': len(cards_by_hash),
        'ste_reassigned': ste_reassigned,
        'significant_features_used': sig_features,
        'redistribution_summary': redistribution_summary
    }

