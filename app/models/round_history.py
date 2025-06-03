from datetime import datetime
from app.extensions import db

class RoundHistory(db.Model):
    __tablename__ = 'round_histories'
    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, db.ForeignKey('games.id'), nullable=False)
    player_id = db.Column(db.Integer, db.ForeignKey('players.id'), nullable=False)
    round = db.Column(db.Integer, nullable=False)
    bet = db.Column(db.Integer, nullable=False)
    action = db.Column(db.String(10), nullable=False)  # "Fold", "Call", "Raise", "All-in", etc.
    street = db.Column(db.String(8), nullable=False)  # "Preflop", "Flop", "Turn", "River"
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<GameHistory Game: {self.game_id}, Player: {self.player_id}, Action: {self.action}, Street: {self.street}>'
