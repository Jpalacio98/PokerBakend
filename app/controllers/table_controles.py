from flask import jsonify, request
from app.services.table_service import create_table,delete_table,get_all_tables,get_table_by_id,update_table, get_table_by_owner_id


def create():
    data = request.json
    try:
        table = create_table(
            name=data.get('name'),
            small_blind=data.get('small_blind'),
            max_players=data.get('max_players'),
            level_id=data.get('level_id'),
            owner_id=data.get('owner_id'),
            required_stack=data.get('required_stack')
        )
        return jsonify({"message": "Table created successfully", "table_id": table.id}), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


def get_all():
    tables = get_all_tables()
    tables_data = [{
        "id": table.id,
        "name": table.name,
        "small_blind": table.blind,
        "max_players": table.max_players,
        "level_id": table.level_id,
        "owner_id": table.owner_id,
        "required_stack": table.required_stack
    } for table in tables]
    return jsonify(tables_data), 200


def get(table_id):
    table = get_table_by_id(table_id)
    if not table:
        return jsonify({"error": "Table not found"}), 404

    table_data = {
        "id": table.id,
        "name": table.name,
        "small_blind": table.blind,
        "max_players": table.max_players,
        "level_id": table.level_id,
        "owner_id": table.owner_id,
        "required_stack": table.required_stack
    }
    return jsonify(table_data), 200

def get_owner(owner_id):
    tables = get_table_by_owner_id(owner_id)
    if not tables:
        return jsonify({"error": "Tables not found"}), 404

    tables_data = [{
        "id": table.id,
        "name": table.name,
        "small_blind": table.blind,
        "max_players": table.max_players,
        "level_id": table.level_id,
        "owner_id": table.owner_id,
        "required_stack": table.required_stack
    } for table in tables]
    return jsonify(tables_data), 200

def update(table_id):
    data = request.json
    try:
        table = update_table(
            table_id=table_id,
            name=data.get('name'),
            small_blind=data.get('small_blind'),
            max_players=data.get('max_players'),
            level_id=data.get('level_id'),
            owner_id=data.get('owner_id'),
            required_stack=data.get('required_stack')
        )
        return jsonify({"message": "Table updated successfully"}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


def delete(table_id):
    try:
        delete_table(table_id)
        return jsonify({"message": "Table deleted successfully"}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
