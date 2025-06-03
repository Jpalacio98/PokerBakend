from datetime import datetime
from app.extensions import db

class GameHistory(db.Model):
    __tablename__ = 'game_histories'
    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, db.ForeignKey('games.id'), nullable=False)
    player_id = db.Column(db.Integer, db.ForeignKey('players.id'), nullable=False)
    round = db.Column(db.Integer, nullable=False)
    pot = db.Column(db.Integer, nullable=False)
    points = db.Column(db.Integer, nullable=False, default=0)
    result = db.Column(db.String(5), nullable=True)  # "Win", "Lose", "leave"
    street = db.Column(db.String(8), nullable=False)  # "Preflop", "Flop", "Turn", "River"
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<GameHistory Game: {self.game_id}, Player: {self.player_id}, Action: {self.action}, Street: {self.street}>'
