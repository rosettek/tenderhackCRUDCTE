from datetime import datetime
from app import db


class Card(db.Model):
    """Модель карточки товара
    
    Карточки группируются по одинаковым значениям значимых характеристик.
    При изменении списка значимых характеристик карточки пересоздаются автоматически.
    """
    __tablename__ = 'cards'
    
    card_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(500), nullable=False)
    description = db.Column(db.Text, nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.category_id'), nullable=True)
    significant_features_hash = db.Column(db.String(64), nullable=True)  # MD5 хэш для быстрой группировки
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Связи
    stes = db.relationship('STE', backref='card', lazy='dynamic')
    significant_features = db.relationship('CardSignificantFeature', backref='card', lazy='dynamic', cascade='all, delete-orphan', order_by='CardSignificantFeature.display_order')
    
    def to_dict(self, include_significant_features=False, include_stes=False):
        result = {
            'card_id': self.card_id,
            'title': self.title,
            'description': self.description,
            'category_id': self.category_id,
            'significant_features_hash': self.significant_features_hash,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'is_active': self.is_active
        }
        
        if include_significant_features:
            result['significant_features'] = [f.to_dict() for f in self.significant_features]
        
        if include_stes:
            result['stes'] = [s.to_dict() for s in self.stes]
            result['ste_count'] = self.stes.count()
        
        return result
    
    def calculate_features_hash(self):
        """Вычислить хэш значимых характеристик карточки"""
        import hashlib
        features_str = '|'.join(
            sorted([f"{f.feature_name}={f.feature_value or ''}" for f in self.significant_features])
        )
        return hashlib.md5(features_str.encode()).hexdigest()
    
    def __repr__(self):
        return f'<Card {self.title}>'

