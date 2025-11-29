from datetime import datetime
from app import db


class STE(db.Model):
    """Модель СТЕ (Стандартная товарная единица)
    
    Все характеристики СТЕ хранятся в поле attributes как JSON объект.
    При пересоздании карточек СТЕ автоматически перегруппировываются по значениям значимых характеристик.
    """
    __tablename__ = 'ste'
    
    ste_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    card_id = db.Column(db.Integer, db.ForeignKey('cards.card_id', ondelete='SET NULL'), nullable=True)
    name = db.Column(db.String(500), nullable=False)
    attributes = db.Column(db.JSON, nullable=False, default=dict)  # Все характеристики в формате {"feature_name": "value"}
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'ste_id': self.ste_id,
            'card_id': self.card_id,
            'name': self.name,
            'attributes': self.attributes or {},
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def get_feature_value(self, feature_name):
        """Получить значение характеристики из attributes"""
        if not self.attributes:
            return None
        return self.attributes.get(feature_name)
    
    def set_feature_value(self, feature_name, value):
        """Установить значение характеристики в attributes"""
        if not self.attributes:
            self.attributes = {}
        self.attributes[feature_name] = value
    
    def __repr__(self):
        return f'<STE {self.name}>'

