from .helpers import (
    session_scope,
    extend_movement_json,
    load_user,
    load_movement,
)
from gridt.models import Movement
from gridt.exc import MovementNotFoundError


def get_all_movements(user_id):
    """Get all movements."""
    with session_scope() as session:
        user = load_user(user_id, session)
        return [
            extend_movement_json(movement, user, session)
            for movement in session.query(Movement)
        ]


def get_movement(movement_identifier, user_id):
    """Get a movement."""
    with session_scope() as session:
        try:
            movement_identifier = int(movement_identifier)
            movement = load_movement(movement_identifier, session)
        except ValueError:
            movement = (
                session.query(Movement)
                .filter_by(name=movement_identifier)
                .one()
            )

        user = load_user(user_id, session)
        return extend_movement_json(movement, user, session)


def movement_exists(movement_id):
    with session_scope() as session:
        try:
            load_movement(movement_id, session)
        except MovementNotFoundError:
            return False
        return True

