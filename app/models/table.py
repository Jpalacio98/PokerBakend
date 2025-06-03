from datetime import datetime
from app.extensions import db

class Table(db.Model):
    __tablename__ = 'tables'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    blind = db.Column(db.Integer, nullable=False)
    level_id = db.Column(db.Integer, db.ForeignKey('levels.id'), nullable=False)
    max_players = db.Column(db.Integer, nullable=False)
    required_stack = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    players = db.relationship('Table_Player', backref='table')
    games = db.relationship('Game', backref='table')

    def __repr__(self):
        return f'<Table {self.name}, Owner: {self.owner_id}, Max Players: {self.max_players}>'