"""
Сервис пересоздания карточек при изменении значимых характеристик
"""
from typing import List, Dict, Optional, Tuple
from app import db
from app.models import Card, STE, CardSignificantFeature, CategoryFeatureTemplate, FeatureChangeLog


def get_features_key(feature_names: List[str], ste_attributes: Dict) -> tuple:
    """Получить ключ группировки на основе значений значимых характеристик"""
    values = []
    for feature_name in sorted(feature_names):
        value = ste_attributes.get(feature_name, '__missing__') if ste_attributes else '__missing__'
        values.append((feature_name, str(value)))
    return tuple(values)


def get_significant_features_for_category(category_id: int, custom_features: Optional[List[str]] = None) -> List[str]:
    """Получить список значимых характеристик для категории"""
    if custom_features:
        return custom_features
    
    # ПРИОРИТЕТ 1: Собираем значимые характеристики из активных карточек категории
    # Это самый надежный источник, так как пользователь явно пометил их как значимые
    active_cards = Card.query.filter_by(
        category_id=category_id,
        is_active=True
    ).all()
    
    if active_cards:
        # Собираем все значимые характеристики из всех активных карточек
        significant_features_set = set()
        for card in active_cards:
            # Получаем из таблицы card_significant_features
            sig_features = CardSignificantFeature.query.filter_by(
                card_id=card.card_id
            ).all()
            for sig_feature in sig_features:
                significant_features_set.add(sig_feature.feature_name)
            
            # Также проверяем поле significant_features_list в карточке
            if card.significant_features_list:
                significant_features_set.update(card.significant_features_list)
        
        if significant_features_set:
            return sorted(list(significant_features_set))
    
    # ПРИОРИТЕТ 2: Получаем из шаблонов категории
    templates = CategoryFeatureTemplate.query.filter_by(
        category_id=category_id,
        is_recommended_significant=True
    ).order_by(CategoryFeatureTemplate.usage_count.desc()).all()
    
    if templates:
        return [t.feature_name for t in templates]
    
    # ПРИОРИТЕТ 3: Если нет шаблонов и нет помеченных характеристик, 
    # собираем все уникальные характеристики из СТЕ категории
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
    
    # Группируем СТЕ по значениям значимых характеристик
    cards_by_key: Dict[tuple, Card] = {}
    redistribution_summary = []
    ste_reassigned = 0
    
    for ste in stes:
        if not ste.attributes:
            continue
        
        # Получаем ключ группировки на основе значений характеристик
        features_key = get_features_key(sig_features, ste.attributes)
        
        # Ищем или создаём карточку с таким ключом
        if features_key not in cards_by_key:
            # Создаём новую карточку
            new_card = Card(
                title=ste.name,
                description=None,
                category_id=category_id,
                significant_features_list=sorted(sig_features),  # Сохраняем список названий характеристик
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
            
            cards_by_key[features_key] = new_card
            
            # Логируем создание новой карточки
            redistribution_summary.append({
                'old_card_id': ste.card_id,
                'new_card_id': new_card.card_id,
                'ste_count': 0  # Будет обновлено ниже
            })
        
        # Привязываем СТЕ к карточке
        old_card_id = ste.card_id
        ste.card_id = cards_by_key[features_key].card_id
        ste_reassigned += 1
        
        # Обновляем счётчик СТЕ в summary
        for summary_item in redistribution_summary:
            if summary_item['new_card_id'] == ste.card_id:
                summary_item['ste_count'] += 1
                break
    
    # Логируем операцию (используем первую созданную карточку для card_id, если есть)
    if cards_by_key:
        first_card_id = list(cards_by_key.values())[0].card_id
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
        'new_cards_created': len(cards_by_key),
        'ste_reassigned': ste_reassigned,
        'significant_features_used': sig_features,
        'redistribution_summary': redistribution_summary
    }

