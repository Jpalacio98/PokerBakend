from app.models.table import Table
from app.models.level import Level
from app import db


def create_table(name, small_blind, max_players, level_id,owner_id,required_stack):
    # Verificar si la ciega pequeña está dentro del rango del nivel
    level = Level.query.get(level_id)
    if not level or not (int(level.blind_min) <= int(small_blind) <= int(level.blind_max)):
        raise ValueError("Small blind is out of the level's range")

    # Crear la mesa
    table = Table(name=name, blind=small_blind, max_players=max_players, level_id=level_id, owner_id=owner_id,required_stack=required_stack)
    db.session.add(table)
    db.session.commit()
    return table


def get_all_tables():
    return Table.query.all()


def get_table_by_id(table_id):
    return Table.query.get(table_id)

def get_table_by_owner_id(owner_id):
    return Table.query.filter_by(owner_id=owner_id).all()



def update_table(table_id, name, small_blind, max_players, level_id,owner_id,required_stack):
    table = Table.query.get(table_id)
    if not table:
        raise ValueError("Table not found")

    # Verificar si la ciega pequeña está dentro del rango del nivel
    level = Level.query.get(level_id)
    if not level or not (level.blind_min <= small_blind <= level.blind_max):
        raise ValueError("Small blind is out of the level's range")

    # Actualizar los campos
    table.name = name
    table.blind = small_blind
    table.max_players = max_players
    table.level_id = level_id
    table.owner_id = owner_id
    table.required_stack = required_stack
    db.session.commit()
    return table


def delete_table(table_id):
    table = Table.query.get(table_id)
    if not table:
        raise ValueError("Table not found")

    db.session.delete(table)
    db.session.commit()
