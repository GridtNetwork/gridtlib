"""Helpers for controllers."""
from contextlib import contextmanager
from gridt.db import Session
from gridt.models import User, Movement
from gridt import exc as GridtExceptions


@contextmanager
def session_scope():
    """
    Context for dealing with sessions.

    This allows the developer not to have to worry perse about closing and
    creating the session.
    """
    session = Session()
    try:
        yield session
        session.commit()
    except:  # noqa: E722
        session.rollback()
        raise
    finally:
        session.close()


def assert_user_is_admin(user_id: int, session: Session) -> None:
    """
    Raise an exception if the user is not an admin.

    Args:
        user_id (int): The user id in question
        session (Session): The session to use for queries

    Raises:
        GridtExceptions.UserNotAdmin: The exception raised.
    """
    user = load_user(user_id, session)
    if not user.is_admin:
        raise GridtExceptions.UserNotAdmin(f"User '{user_id}' not an admin")


def load_user(user_id: int, session: Session) -> User:
    """Load a user from the database."""
    user = session.get(User, user_id)
    if not user:
        raise GridtExceptions.UserNotFoundError(
            f"No ID '{user_id}' not found."
        )
    return user


def load_movement(movement_id: int, session: Session) -> Movement:
    """Load a movement from the database."""
    movement = session.get(Movement, movement_id)
    if not movement:
        raise GridtExceptions.MovementNotFoundError(
            f"No ID '{movement_id}' not found."
        )
    return movement
