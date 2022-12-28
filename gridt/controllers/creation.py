from gridt.models import Creation
from sqlalchemy.orm.query import Query
from gridt.db import Session
from .helpers import (
    session_scope,
    load_movement,
    load_user,
    extend_movement_json
)

def _get_creation(user_id: int, movement_id: int, session: Session) -> Query:
    """
    Helper function to get creation relation

    Args:
        user_id (int): The id of the user
        movement_id (int): The id of the movement
        session (Session): The session to communicate with the DB

    Returns:
        Query: A creation relation query 
    """
    return (
        session.query(Creation)
        .filter_by(
            Creation.user_id == user_id,
            Creation.movement_id == movement_id,
            Creation.time_removed.is_(None)
        )
        .one()
    )


def is_creator(user_id: int, movement_id: int) -> bool:
    """
    Checks if a user is the creator of a movement

    Args:
        user_id (int): The user id
        movement_id (int): The movement id

    Returns:
        bool: True if the user has created the movement, otherwise False
    """
    with session_scope() as session:
        try:
            _get_creation(user_id, movement_id, session)
        except:
            return False

    return True


def new_creation(user_id: int, movement_id: int) -> dict:
    """
    Creates a new creation relation between a user and movement.

    Args:
        user_id (int): The id of the user
        movement_id (int): The id of the movement

    Returns:
        dict: json representation of the new subscription
    """
    with session_scope() as session:
        user = load_user(user_id)
        movement = load_movement(movement_id)
        
        creation = Creation(user, movement)
        session.add(creation)
    
        #TODO: should have an emit listener here to actually create the movement

    return creation.to_json()


def remove_creation(user_id: int, movement_id: int) -> dict:
    """
    Ends a creation relation between a user and a movement.

    Args:
        user_id (int): The id of the user
        movement_id (int): The id of the movement

    Returns:
        dict: json of the removed creation relation
    """
    with session_scope() as session:
        creation = _get_creation(user_id, movement_id, session)
        creation.end()

        #TODO: should have an emit listener to actually remove the movement

    return creation.to_json()