from app.extensions import db
from datetime import datetime

class Game(db.Model):
    __tablename__ = 'games'
    id = db.Column(db.Integer, primary_key=True)
    table_id = db.Column(db.Integer, db.ForeignKey('tables.id'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    end_time = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    histories = db.relationship('GameHistory', backref='game')

    def __repr__(self):
        return f'<Game {self.id}, Table: {self.table_id}, Start: {self.start_time}>'
