from .helpers import session_scope, load_movement, load_user, leaders
from gridt.models import Signal, User, Movement
from gridt.models import UserToUserLink

from gridt.controllers.subscription import on_subscription, on_unsubscription, is_subscribed
from gridt.controllers import follower as Follower

import random

from sqlalchemy.orm.query import Query
from sqlalchemy import not_
from sqlalchemy.orm.session import Session


def _add_initial_followers(leader_id: int, movement_id: int) -> None:
    """
    This funciton adds the initial followers of a leader joining a movement

    Args:
        leader_id (int): The id of the leader who just joined the movement
        movement_id (int): The id of the movement itself
    """
    with session_scope() as session:
        user = load_user(leader_id, session)
        movement = load_movement(movement_id, session)

        # Give that new subscriber other followers to follow in the movement
        for new_follower in Follower.possible_followers(user, movement, session):
            user_to_user_link = UserToUserLink(movement, new_follower, leader=user)
            session.add(user_to_user_link)

            # Remove any None associations the new follower may have had
            assoc_none = (
                session.query(UserToUserLink)
                .filter(
                    UserToUserLink.movement_id == movement.id,
                    UserToUserLink.follower_id == new_follower.id,
                    UserToUserLink.leader_id.is_(None),
                )
                .group_by(UserToUserLink.follower_id)
                .all()
            )
            for a in assoc_none:
                a.destroy()
    


# Add a listener to new subscription event to get the initial followers
on_subscription(_add_initial_followers)


def _remove_all_followers(leader_id: int, movement_id: int) -> None:
    """
    This funciton removes all follower of a leader upon leaving a movment.
    It then tries to assign new leaders to followers.

    Args:
        leader_id (int): The id of the leader who just left the movement
        movement_id (int): The id of the movement itself
    """
    with session_scope() as session:
        movement = load_movement(movement_id, session)

        # Remove all links to the removed subscriber
        leader_user_to_user_links_to_destroy = session.query(UserToUserLink).filter(
            UserToUserLink.movement_id == movement_id,
            UserToUserLink.destroyed.is_(None),
            UserToUserLink.leader_id == leader_id,
        ).all()

        for user_to_user_link in leader_user_to_user_links_to_destroy:
            user_to_user_link.destroy()

        session.commit()

        # For each follower removed try to find a new leader
        for user_to_user_link in leader_user_to_user_links_to_destroy:
            poss_new_leaders = possible_leaders(user_to_user_link.follower, user_to_user_link.movement, session).all()
            poss_new_leaders = [l for l in poss_new_leaders if l.id != leader_id]
            # Add new MovementToMovementLinks for each former follower.
            if poss_new_leaders:
                new_leader = random.choice(poss_new_leaders)
                new_user_to_user_link = UserToUserLink(
                    movement, user_to_user_link.follower, new_leader
                )
                session.add(new_user_to_user_link)
            else:
                new_user_to_user_link = UserToUserLink(movement, user_to_user_link.follower, None)
                session.add(new_user_to_user_link)


# Add a listener to remove subscription event to remove all the followers for a leader.
on_unsubscription(_remove_all_followers)


def send_signal(leader_id: int, movement_id: int, message: str = None):
    """Send signal as a leader in a movement, optionally with a message."""
    with session_scope() as session:
        leader = load_user(leader_id, session)
        movement = load_movement(movement_id, session)

        assert is_subscribed(leader_id, movement_id)

        signal = Signal(leader, movement, message)
        session.add(signal)
        session.commit()


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
            UserToUserLink.movement_id == movement.id,
            UserToUserLink.destroyed.is_(None)
        )
        .group_by(User.id)
    )