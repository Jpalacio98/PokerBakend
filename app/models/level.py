from datetime import datetime
from app.extensions import db

class Level(db.Model):
    __tablename__ = 'levels'
    id = db.Column(db.Integer, primary_key=True,autoincrement=True )
    name = db.Column(db.String(50), nullable=False)
    blind_min = db.Column(db.Integer, nullable=False)
    blind_max = db.Column(db.Integer, nullable=False)
    required_points = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    players = db.relationship('Player', backref='level')

    def __repr__(self):
        return f'<Level {self.name}, Blind Range: {self.blind_min}-{self.blind_max}>'
