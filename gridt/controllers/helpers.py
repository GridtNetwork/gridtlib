from contextlib import contextmanager
from sqlalchemy import not_, desc
from sqlalchemy.orm.query import Query
from gridt.db import Session
from gridt.models import User, MovementUserAssociation, Movement, Signal
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
        .join(MovementUserAssociation.leader)
        .filter(
            MovementUserAssociation.follower_id == user.id,
            MovementUserAssociation.movement_id == movement.id,
            not_(MovementUserAssociation.leader_id.is_(None)),
            MovementUserAssociation.destroyed.is_(None),
        )
    )


def possible_leaders(
    user: User, movement: Movement, session: Session
) -> Query:
    """Find possible leaders for a user in a movement."""
    return (
        session.query(User)
        .join(User.follower_associations)
        .filter(
            not_(User.id == user.id),
            not_(
                User.id.in_(
                    leaders(user, movement, session).with_entities(User.id)
                )
            ),
            MovementUserAssociation.movement_id == movement.id,
        )
        .group_by(User.id)
    )


def possible_followers(
    user: User, movement: Movement, session: Session
) -> Query:
    """
    Find the active users in this movement
    (movement.current_users) that have fewer than four leaders,
    excluding the current user or any of his followers.

    :param user User that would be the possible leader
    :param movement Movement where the leaderless are queried
    :param session Session in which the query is performed
    """
    MUA = MovementUserAssociation

    leader_associations = session.query(MUA.follower_id).filter(
        MUA.movement_id == movement.id, MUA.leader_id == user.id
    )

    available_leaderless = movement.leaderless.filter(
        not_(User.id == user.id), not_(User.id.in_(leader_associations))
    )

    return available_leaderless


def find_last_signal(
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
    if user in movement.active_users:
        movement_json["subscribed"] = True

        last_signal = find_last_signal(user, movement, session)
        movement_json["last_signal_sent"] = (
            last_signal.to_json() if last_signal else None
        )

        movement_json["leaders"] = []
        for leader in leaders(user, movement, session):
            leader_json = leader.to_json()

            last_leader_signal = find_last_signal(leader, movement, session)
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
