from contextlib import contextmanager
from sqlalchemy import not_
from sqlalchemy.orm.query import Query
from gridt.db import Session
from gridt.models import User, MovementUserAssociation, Movement


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

    available_leaderless = movement.leaderless.filter(
        not_(User.id == user.id),
        not_(User.id.in_(leader_associations))
    )

    return available_leaderless
