from datetime import datetime
from app import db


class CardSignificantFeature(db.Model):
    """Модель значимых характеристик карточки
    
    Ключевая модель! Список значимых характеристик определяет группировку СТЕ в карточки.
    При изменении этого списка карточки автоматически пересоздаются.
    """
    __tablename__ = 'card_significant_features'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    card_id = db.Column(db.Integer, db.ForeignKey('cards.card_id', ondelete='CASCADE'), nullable=False)
    feature_name = db.Column(db.String(255), nullable=False)
    feature_value = db.Column(db.String(1000), nullable=True)
    display_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Уникальный индекс
    __table_args__ = (
        db.UniqueConstraint('card_id', 'feature_name', name='unique_card_feature'),
        db.Index('idx_card_sig_features_card', 'card_id'),
        db.Index('idx_card_sig_features_name', 'feature_name'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'card_id': self.card_id,
            'feature_name': self.feature_name,
            'feature_value': self.feature_value,
            'display_order': self.display_order,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<CardSignificantFeature card_id={self.card_id} {self.feature_name}={self.feature_value}>'


class CategoryFeatureTemplate(db.Model):
    """Модель шаблонов значимых характеристик по категориям
    
    Справочная таблица для подсказок и рекомендаций.
    Не влияет напрямую на группировку, но используется при автоматическом пересоздании карточек.
    """
    __tablename__ = 'category_feature_templates'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.category_id', ondelete='CASCADE'), nullable=False)
    feature_name = db.Column(db.String(255), nullable=False)
    is_recommended_significant = db.Column(db.Boolean, default=True)
    usage_count = db.Column(db.Integer, default=0)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Уникальный индекс
    __table_args__ = (
        db.UniqueConstraint('category_id', 'feature_name', name='unique_category_feature_template'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'category_id': self.category_id,
            'feature_name': self.feature_name,
            'is_recommended_significant': self.is_recommended_significant,
            'usage_count': self.usage_count,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<CategoryFeatureTemplate category_id={self.category_id} {self.feature_name} recommended={self.is_recommended_significant}>'

