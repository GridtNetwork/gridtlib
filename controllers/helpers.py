from contextlib import contextmanager
from sqlalchemy import not_, or_, func
from sqlalchemy.orm.query import Query
from db import Session
from models import User, MovementUserAssociation, Movement


@contextmanager
def session_scope():
    """
    Context for dealing with sessions. This allows the developer not to have to
    worry perse about closing and creating the session.
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


def get_current_users(movement: Movement, session: Session) -> Query:
    """
    Get all the users subscribed to a movement.

    :param movement The relevant movement
    :param session The session the query needs to be performed in
    """
    return (
        session.query(User)
        .join(User.follower_associations)
        .filter(
            MovementUserAssociation.movement_id == movement.id,
            MovementUserAssociation.destroyed.is_(None),
        )
        .group_by(User.id)
    )


def get_current_movements(user: User, session: Session) -> Query:
    return (
        session.query(Movement)
        .join(Movement.user_associations)
        .filter(
            or_(
                MovementUserAssociation.follower_id == user.id,
                MovementUserAssociation.leader_id == user.id
            ),
            MovementUserAssociation.destroyed.is_(None)
        )
    )


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
    """
    Find possible leaders for a user in a movement.
    """
    return (
        session.query(User)
        .join(User.follower_associations)
        .filter(
            not_(User.id == user.id),
            not_(
                User.id.in_(
                    leaders(user, movement, session).with_entities(
                        User.id
                    )
                )
            ),
            MovementUserAssociation.movement_id == movement.id,
        )
        .group_by(User.id)
    )


def leaderless(user: User, movement: Movement, session: Session) -> Query:
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

    valid_muas = (
        session.query(
            MUA,
            func.count().label("mua_count"),
        )
        .filter(
            MUA.movement_id == movement.id,
            MUA.destroyed.is_(None),
        )
        .group_by(MUA.follower_id)
        .subquery()
    )

    leaderless = (
        session.query(User)
        .join(User.follower_associations)
        .filter(
            not_(User.id == user.id),
            valid_muas.c.follower_id == User.id,
            valid_muas.c.mua_count < 4,
        )
        .group_by(MUA.follower_id)
        .filter(not_(User.id.in_(leader_associations)))
    )

    return leaderless
