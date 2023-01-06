from gridt.models import Creation, Movement
import gridt.exc as E
from .helpers import (
    session_scope,
    load_movement,
    load_user
)

from sqlalchemy.orm.query import Query
from sqlalchemy.orm.session import Session

import types

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
    creations = (
        session.query(Creation)
        .filter(
            Creation.user_id == user_id,
            Creation.movement_id == movement_id,
            Creation.time_removed.is_(None)
        )
    )

    if not creations.count():
        raise E.UserIsNotCreator(f"User '{user_id}' has not created the Movement '{movement_id}'. Or one or both do not exist")
    
    return creations.one()


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
        except E.UserIsNotCreator:
            return False

    return True


# set of events to listening to the creation of a movement
_on_create_events = set()


def on_creation(event_func: types.FunctionType) -> None:
    """
    This function adds an event listener to the function new_creation.

    Args:
        event_func (types.FunctionType): A function that should be called whenever a creation relation is made between users and movements.
        The function should be in the type (user_id: int, movement_id: int) -> None.
    """
    _on_create_events.add(event_func)


def _notify_creation_listeners(user_id: int, movement_id: int) -> None:
    """
    This helper function calls all event functions for each listener.

    Args:
        user_id (int): The id of the user who created a new movement.
        movement_id (int): The id of the movement who was just created.
    """
    for event in _on_create_events:
        event(user_id, movement_id)


def new_movement_by_user(
    user_id: int,
    name: str,
    interval: str,
    short_description: str = None,
    description: str = None,
) -> dict:
    """Creates a new movement by a user. With the given user as the creator.

    Args:
        user_id (int): The id of the user creating the movement
        name (str): The name of the movement
        interval (str): The signal interval the new movement should have.
        short_description (str, optional): Short summary of the new movement. Defaults to None.
        description (str, optional): Opitonal more in depth description of the new movment. Defaults to None.

    Returns:
        dict: json representation of the new creation

    TODO:
        Maybe move this function to movement controller idk
    """
    with session_scope() as session:
        movement = Movement(name, interval, short_description, description)
        session.add(movement)
        session.commit()
        movement_id = movement.id
    
    return _new_creation(user_id, movement_id)


def _new_creation(user_id: int, movement_id: int) -> dict:
    """
    Creates a new creation relation between a user and movement.

    Args:
        user_id (int): The id of the user
        movement_id (int): The id of the movement

    Returns:
        dict: json representation of the new creation
    """
    with session_scope() as session:
        user = load_user(user_id, session)
        movement = load_movement(movement_id, session)
        creation = Creation(user, movement)

        session.add(creation)
        creation_json = creation.to_json()
    
    # Emit message to all listeners
    _notify_creation_listeners(user_id, movement_id)

    return creation_json


# set of events to listening to the removal of a movement
_on_remove_creation_events = set()


def on_remove_creation(event_func: types.FunctionType) -> None:
    """
    This function adds an event listener to the function remove_creation.

    Args:
        event_func (types.FunctionType): A function that should be called whenever a creation relation is removed.
        The function should be in the type (user_id: int, movement_id: int) -> None
    """
    _on_remove_creation_events.add(event_func)


def _notify_remove_creation_listeners(user_id: int, movement_id: int) -> None:
    """
    This helper function calls all notify functions for each listener.

    Args:
        user_id (int): The id of the user who relation to the movement was removed.
        movement_id (int): The id of the movement who relation to the user was removed.
    """
    for event in _on_remove_creation_events:
        event(user_id, movement_id)


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

        session.add(creation)
        removed_json = creation.to_json()

    # Emit event to listeners
    _notify_remove_creation_listeners(user_id, movement_id)

    return removed_json
