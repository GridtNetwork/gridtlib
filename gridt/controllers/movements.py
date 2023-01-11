from .helpers import (
    session_scope,
    extend_movement_json,
    load_user,
    load_movement,
)
from gridt.models import Movement
from gridt.exc import MovementNotFoundError


def create_movement(
    name: str,
    interval: str,
    short_description: str = None,
    description: str = None,
) -> dict:
    """
    Creates a new movement.

    Args:
        name (str): The name of the movement
        interval (str): The signal interval the new movement should have.
        short_description (str, optional): Short summary of the new movement. Defaults to None.
        description (str, optional): Opitonal more in depth description of the new movment. Defaults to None.

    Returns:
        dict: json representation of the new movement
    """
    with session_scope() as session:
        movement = Movement(name, interval, short_description, description)
        session.add(movement)
        session.commit()
        movement_json = movement.to_json()
    
    return movement_json


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

