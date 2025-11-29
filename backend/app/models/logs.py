from datetime import datetime
from app import db


class FeatureChangeLog(db.Model):
    """Модель лога изменений характеристик"""
    __tablename__ = 'feature_change_logs'
    
    log_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    operation = db.Column(db.String(50), nullable=False)  # mark_significant, mark_insignificant, change_value, add_feature, remove_feature
    ste_id = db.Column(db.Integer, db.ForeignKey('ste.ste_id', ondelete='SET NULL'), nullable=True)
    card_id = db.Column(db.Integer, db.ForeignKey('cards.card_id', ondelete='CASCADE'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.category_id', ondelete='SET NULL'), nullable=True)
    feature_name = db.Column(db.String(255), nullable=False)
    old_value = db.Column(db.String(1000), nullable=True)
    new_value = db.Column(db.String(1000), nullable=True)
    became_significant = db.Column(db.Boolean, nullable=True)
    became_insignificant = db.Column(db.Boolean, nullable=True)
    moderator_id = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    comment = db.Column(db.Text, nullable=True)
    
    # Индексы
    __table_args__ = (
        db.Index('idx_feature_logs_card', 'card_id'),
        db.Index('idx_feature_logs_operation', 'operation'),
        db.Index('idx_feature_logs_created', 'created_at'),
    )
    
    def to_dict(self):
        return {
            'log_id': self.log_id,
            'operation': self.operation,
            'ste_id': self.ste_id,
            'card_id': self.card_id,
            'category_id': self.category_id,
            'feature_name': self.feature_name,
            'old_value': self.old_value,
            'new_value': self.new_value,
            'became_significant': self.became_significant,
            'became_insignificant': self.became_insignificant,
            'moderator_id': self.moderator_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'comment': self.comment
        }
    
    def __repr__(self):
        return f'<FeatureChangeLog {self.operation} on {self.feature_name}>'


class CardMergeLog(db.Model):
    """Модель лога объединения карточек"""
    __tablename__ = 'card_merge_logs'
    
    merge_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    operation = db.Column(db.String(50), default='merge_cards')
    from_card_ids = db.Column(db.JSON, nullable=False)
    to_card_id = db.Column(db.Integer, db.ForeignKey('cards.card_id'), nullable=False)
    affected_ste_ids = db.Column(db.JSON, nullable=False)
    moderator_id = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    comment = db.Column(db.Text, nullable=True)
    
    # Индексы
    __table_args__ = (
        db.Index('idx_merge_logs_to_card', 'to_card_id'),
        db.Index('idx_merge_logs_created', 'created_at'),
    )
    
    def to_dict(self):
        return {
            'merge_id': self.merge_id,
            'operation': self.operation,
            'from_card_ids': self.from_card_ids,
            'to_card_id': self.to_card_id,
            'affected_ste_ids': self.affected_ste_ids,
            'moderator_id': self.moderator_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'comment': self.comment
        }
    
    def __repr__(self):
        return f'<CardMergeLog merge to card {self.to_card_id}>'

