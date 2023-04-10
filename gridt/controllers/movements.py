"""Controller for Movements."""
from .helpers import (
    session_scope,
    load_user,
    load_movement,
    GridtExceptions
)
from gridt.models import Movement
from gridt.controllers import subscription as Subscription
from gridt.controllers import announcement as Announcement

from sqlalchemy.orm import Session


def create_movement(
    name: str,
    interval: str,
    short_description: str,
    description: str,
    session: Session,
) -> Movement:
    """
    Create a new movement.

    Args:
        name (str): The name of the movement
        interval (str): The signal interval the new movement should have.
        short_description (str, optional): Short summary of the new movement.
        description (str, optional): More in depth description.
        session (Session): sqlalchmey session to communicate with DB.

    Returns:
        dict: json representation of the new movement
    """
    movement = Movement(name, interval, short_description, description)
    session.add(movement)
    session.commit()
    return movement


def get_all_movements(user_id):
    """Get all movements."""
    with session_scope() as session:
        user = load_user(user_id, session)
        return [
            extend_movement_json(movement, user, session)
            for movement in session.query(Movement)
        ]


def get_movement(movement_id: int, user_id: int) -> dict:
    """
    Get a movement as user.

    Args:
        movement_id (int): The id of the movement to get.
        user_id (int): The id of the user to get movement as.

    Returns:
        dict: the JSON representation of the movement.
    """
    with session_scope() as session:
        user = load_user(user_id, session)
        movement = load_movement(movement_id, session)
        return extend_movement_json(movement, user, session)


def movement_name_exists(movement_name: str) -> bool:
    """
    Is the provided movement name currently in use.

    Args:
        movement_name (str): The movement name as a string.

    Returns:
        bool: True if a movement already has this name, and False otherwise.
    """
    with session_scope() as session:
        movement = session.query(Movement).filter_by(
            name=movement_name
        ).one_or_none()

        return (movement is not None)


def movement_exists(movement_id):
    """Check if a movement exists through an expection otherwise."""
    with session_scope() as session:
        try:
            load_movement(movement_id, session)
        except GridtExceptions.MovementNotFoundError:
            return False
        return True


def extend_movement_json(movement, user, session) -> dict:
    """
    Extend the json for a movement with additional information.

    Args:
        movement (Movement): The movement itself.
        user (User): The user to retrieve the information for.
        session (Session): The session.

    Returns:
        dict: extended movement JSON as python dict
    """
    movement_json = movement.to_json()
    movement_json["subscribed"] = False

    if Subscription._subscription_exists(user.id, movement.id, session):
        movement_json["subscribed"] = True
        Announcement.add_json_announcement_details(
            movement_json, movement, session
        )
        Subscription.add_json_subscription_details(
            movement_json, movement, user, session
        )

    return movement_json
