"""Controller for annoucements in gridt movements."""
from .helpers import (
    session_scope,
    load_movement,
    load_user,
    GridtExceptions,
    assert_user_is_admin,
)

from gridt.models import Announcement

from sqlalchemy.orm.session import Session
from sqlalchemy.exc import NoResultFound


def create_announcement(message: str, movement_id: int, user_id: int) -> dict:
    """
    Create a new announcement, orginating from a user.

    Args:
        message (str): The message in the announcement
        movement_id (int): The movement id to add an announcement to.
        user_id (int): The id of the user which is creating the announcement.

    Returns:
        dict: The JSON representation of the new announcement
    """
    with session_scope() as session:
        assert_user_is_admin(user_id, session)
        movement = load_movement(movement_id, session)
        user = load_user(user_id, session)
        announcement = Announcement(
            movement=movement,
            message=message,
            user=user
        )
        session.add(announcement)
        session.commit()
        announcement_json = announcement.to_json()

    return announcement_json


def _get_announcement(announcement_id: int, session: Session) -> Announcement:
    """
    Return announcement from the database.

    Args:
        announcement_id (int): The id of the announcement in question
        session (Session): The sqlAlchemy session that should be used

    Raises:
        GridtExceptions.AnnouncementNotFoundError: No announcement with that id

    Returns:
        Announcement: The announcement object
    """
    try:
        return session.query(Announcement).filter(
            Announcement.id == announcement_id,
            Announcement.removed_time.is_(None)
        ).one()
    except NoResultFound:
        raise GridtExceptions.AnnouncementNotFoundError


def update_announcement(message: str, announcement_id: int, user_id: int):
    """
    Update a announcement through a user.

    Args:
        message (str): The new message that should replace the old message.
        announcement_id (int): The id of the announcement to update.
        user_id (int): The user updating the announcement
    """
    with session_scope() as session:
        assert_user_is_admin(user_id, session)
        load_user(user_id, session)
        announcement = _get_announcement(announcement_id, session)
        announcement.update_message(message)


def delete_announcement(announcement_id: int, user_id: int) -> None:
    """
    Delete an announcement through a user.

    Args:
        announcement_id (int): The id of the announcment that has been deleted.
        user_id (int): The user deleting the announcement
    """
    with session_scope() as session:
        assert_user_is_admin(user_id, session)
        load_user(user_id, session)
        announcement = _get_announcement(announcement_id, session)
        announcement.remove()


def get_announcements(movement_id: int) -> list:
    """
    Get list of announcement in a movement.

    Args:
        movement_id (int): The id of the movement in question

    Returns:
        list: List of all the announcements (JSON) of a movement
    """
    with session_scope() as session:
        movement_announcements = session.query(Announcement).filter(
            Announcement.movement_id == movement_id,
            Announcement.removed_time.is_(None)
        ).order_by(Announcement.created_time.desc()).all()
        announcements_jsons = [a.to_json() for a in movement_announcements]

    return announcements_jsons


def add_json_announcement_details(json: dict, movement, session: Session):
    """
    Add movement details about latest annoucement for a movement.

    Args:
        json (dict): The json to construct
        movement (Movement): The movement
        session (Session): The sqlAlchemy session to use
    """
    announcement = session.query(Announcement).filter(
        Announcement.movement_id == movement.id,
        Announcement.removed_time.is_(None)
    ).order_by(Announcement.created_time.desc()).first()

    if announcement:
        json['last_announcement'] = announcement.to_json()
    else:
        json['last_announcement'] = None
