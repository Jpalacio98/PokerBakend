from datetime import datetime
from app.extensions import db


class Player(db.Model):
    __tablename__ = 'players'
    id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    level_id = db.Column(db.Integer, db.ForeignKey('levels.id'))
    balance = db.Column(db.Integer, nullable=False, default=1000)
    stack = db.Column(db.Integer, nullable=False, default=0)
    total_points = db.Column(db.Integer, nullable=False, default=0)  # Total points earned in all games
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    tables = db.relationship('Table_Player', backref='player')
    histories = db.relationship('GameHistory', backref='player')

    def __repr__(self):
        return f'<Player {self.id}, Stack: {self.stack}, Points: {self.total_points}>'
    
    def update_points_and_level(self, points: int):
        """
        Suma puntos al jugador, y actualiza el nivel según su total de puntos.
        Si baja de puntos, también puede bajar de nivel.
        """
        from app.models.level import Level  # Asegúrate que el modelo Level esté importado correctamente

        # Actualizar puntos
        self.total_points += points

        # Obtener todos los niveles ordenados por required_points ascendente
        levels = Level.query.order_by(Level.required_points).all()

        new_level = None
        for level in levels:
            if self.total_points >= level.required_points:
                new_level = level
            else:
                break  # ya no alcanza el siguiente nivel

        if new_level and self.level_id != new_level.id:
            self.level_id = new_level.id
            print(f"Player {self.id} now has level {new_level.name}")
            
    def deduct_balance_for_table(self, table) -> bool:
        """
        Resta del balance del jugador el costo de entrada de la mesa.
        Retorna True si la operación fue exitosa, False si no hay suficiente balance.
        """
        entry_fee = table.get('required_stack',None)
        print(entry_fee)
        if entry_fee is None:
            raise ValueError("La mesa no tiene definido un 'required_stack'.")

        if self.balance >= entry_fee:
            self.balance -= entry_fee
            return True
        else:
            print(f"Player {self.id} no tiene suficiente balance para unirse a la mesa.")
            return False
    
    def set_balance(self, cash,table_stack):
        self.stack = cash
        self.balance += cash + table_stack
        
