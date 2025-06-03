from datetime import datetime
from app.extensions import db


class Table_Player(db.Model):
    __tablename__ = 'table_players'
    table_id = db.Column(db.Integer, db.ForeignKey('tables.id'), primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey('players.id'), primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Table_Player Table: {self.table_id}, Player: {self.player_id}>'