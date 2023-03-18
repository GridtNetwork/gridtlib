"""Controller for movement creation."""
from gridt.models import Creation
from gridt.controllers import (
    subscription as Subscription,
    movements as Movements
)
from .helpers import (
    session_scope,
    load_movement,
    load_user,
    GridtExceptions,
    assert_user_is_admin,
)

from sqlalchemy.orm.query import Query
from sqlalchemy.orm.session import Session


def _get_creation(user_id: int, movement_id: int, session: Session) -> Query:
    """
    Get creation relation between user and movement.

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
        raise GridtExceptions.UserIsNotCreator(
            f"User '{user_id}' has not",
            f"created the Movement '{movement_id}'.",
            "Or one or both do not exist"
        )

    return creations.one()


def is_creator(user_id: int, movement_id: int) -> bool:
    """
    Check if a user is the creator of a movement.

    Args:
        user_id (int): The user id
        movement_id (int): The movement id

    Returns:
        bool: True if the user has created the movement, otherwise False
    """
    with session_scope() as session:
        try:
            _get_creation(user_id, movement_id, session)
        except GridtExceptions.UserIsNotCreator:
            return False

    return True


def new_movement_by_user(
    user_id: int,
    name: str,
    interval: str,
    short_description: str = None,
    description: str = None,
    auto_subscribe: bool = True
) -> dict:
    """
    Create a new movement by a user (as creator).

    Args:
        user_id (int): The id of the user creating the movement
        name (str): The name of the movement
        interval (str): The signal interval the new movement should have.
        short_description (str, optional): Short summary of the new movement.
        description (str, optional): In depth description of the new movment.
        auto_subscribe (bool, optional): The user is automatically subscribed.

    Returns:
        dict: json representation of the new creation
    """
    movement_json = Movements.create_movement(
        name=name,
        interval=interval,
        short_description=short_description,
        description=description
    )
    movement_id = movement_json['id']

    with session_scope() as session:
        assert_user_is_admin(user_id, session)
        user = load_user(user_id, session)
        movement = load_movement(movement_id, session)
        creation = Creation(user, movement)

        session.add(creation)
        creation_json = creation.to_json()

    if auto_subscribe:
        Subscription.new_subscription(user_id, movement_id)

    return creation_json


def remove_creation(user_id: int, movement_id: int) -> dict:
    """
    End a creation relation between a user and a movement.

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

    return removed_json
