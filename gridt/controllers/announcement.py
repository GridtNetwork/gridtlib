from .helpers import (
    session_scope,
    load_movement,
    load_user
)

from gridt.models import Announcement

def create_announcement(message: str, movement_id: int, user_id: int) -> dict:
    """
    This function creates a new announcement from a user.

    Args:
        message (str): The message in the announcement
        movement_id (int): The id of the movement which should have the announcement.
        user_id (int): The id of the user which is creating the announcement.

    Returns:
        dict: The JSON representation of the new announcement
    
    TODO:
        Check that the user is an admin here!
    """
    with session_scope() as session:
        movement = load_movement(movement_id, session)
        user = load_user(user_id, session)
        announcement = Announcement(movement=movement, message=message, user=user)
        session.add(announcement)
        session.commit()
        announcement_json = announcement.to_json()

    return announcement_json


def update_announcement(message: str, announcement_id: int, user_id: int) -> dict:
    """
    This function updates an announcement from user.

    Args:
        message (str): The new message that should replace the old annoucement text.
        announcement_id (int): The id of the announcement that should be updated.
        user_id (int): The user updating the announcement

    Returns:
        dict: The JSON representation of the announcement before update

    TODO:
        Check that the user is an admin here!
    """
    with session_scope() as session:
        announcement = session.query(Announcement).filter(
            Announcement.id == announcement_id,
            Announcement.removed_time.is_(None)
        ).one()
        announcement_json = announcement.to_json()
        announcement.update_message(message)

    return announcement_json


def delete_announcement(announcement_id: int, user_id: int) -> dict:
    """
    This function deletes an announcement from a user.

    Args:
        announcement_id (int): The id of the announcment that has been deleted.
        user_id (int): The user deleting the announcement

    Returns:
        dict: The announcement that has just been deleted in json.

    TODO:
        Check that the user is an admin here!
    """
    with session_scope() as session:
        announcement = session.query(Announcement).filter(
            Announcement.id == announcement_id
        ).one()
        announcement_json = announcement.to_json()
        announcement.remove()

    return announcement_json


def get_announcements(movement_id: int) -> list:
    """
    This function gets the announcements in a movement

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


def add_json_announcement_details(json: dict, movement, session) -> None:
    """
    This function adds the latest announcement details for a movement

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
