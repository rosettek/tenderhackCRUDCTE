from datetime import datetime
from app import db


class Category(db.Model):
    """Модель категории товаров"""
    __tablename__ = 'categories'
    
    category_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('categories.category_id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Связи
    parent = db.relationship('Category', remote_side=[category_id], backref='children')
    cards = db.relationship('Card', backref='category', lazy='dynamic')
    
    def to_dict(self):
        return {
            'category_id': self.category_id,
            'name': self.name,
            'parent_id': self.parent_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<Category {self.name}>'

