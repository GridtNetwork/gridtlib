from contextlib import contextmanager
from sqlalchemy import not_, desc
from sqlalchemy.orm.query import Query
from gridt.db import Session
from gridt.models import User, UserToUserLink, Movement, Signal, Subscription
from gridt.exc import UserNotFoundError, MovementNotFoundError


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


def leaders(user: User, movement: Movement, session: Session) -> Query:
    """
    Create a query for the leaders of a user in a movement from a session.

    :param gridt.models.user.User user: User that needs new leaders.
    :param list exclude: List of users (can be a user model or an id) to
    exclude from search.
    :returns: Query object
    """
    return (
        session.query(User)
        .join(UserToUserLink.leader)
        .filter(
            UserToUserLink.follower_id == user.id,
            UserToUserLink.movement_id == movement.id,
            not_(UserToUserLink.leader_id.is_(None)),
            UserToUserLink.destroyed.is_(None),
        )
    )


def _find_last_signal(
    leader: User, movement: Movement, session: Session
) -> Signal:
    """Find the last signal the leader has sent to the movement."""
    return (
        session.query(Signal)
        .filter_by(leader=leader, movement=movement)
        .order_by(desc("time_stamp"))
        .first()
    )


def extend_movement_json(movement, user, session):
    movement_json = movement.to_json()
    movement_json["subscribed"] = False

    is_subscribed = (
        session.query(Subscription)
        .filter(
            Subscription.user_id == user.id,
            Subscription.movement_id == movement.id,
            Subscription.time_removed.is_(None)
        ).count()
    )
    
    if is_subscribed:
        movement_json["subscribed"] = True

        last_signal = _find_last_signal(user, movement, session)
        movement_json["last_signal_sent"] = (
            last_signal.to_json() if last_signal else None
        )

        movement_json["leaders"] = []
        for leader in leaders(user, movement, session):
            leader_json = leader.to_json()

            last_leader_signal = _find_last_signal(leader, movement, session)
            if last_leader_signal:
                leader_json.update(last_signal=last_leader_signal.to_json())

            movement_json["leaders"].append(leader_json)
    return movement_json


def load_user(user_id: int, session: Session) -> User:
    """Load a user from the database."""
    user = session.query(User).get(user_id)
    if not user:
        raise UserNotFoundError(f"No ID '{user_id}' not found.")
    return user


def load_movement(movement_id: int, session: Session) -> Movement:
    """Load a movement from the database."""
    movement = session.query(Movement).get(movement_id)
    if not movement:
        raise MovementNotFoundError(f"No ID '{movement_id}' not found.")
    return movement
