from .helpers import session_scope, load_movement, load_user
from gridt.models import Signal, User, Movement
from gridt.models import UserToUserLink

from gridt.controllers import follower as Follower
from gridt.controllers import subscription as Subscription

import random

from sqlalchemy.orm.query import Query
from sqlalchemy import not_, desc
from sqlalchemy.orm.session import Session


def add_initial_followers(leader_id: int, movement_id: int) -> None:
    """
    This function adds the initial followers of a leader joining a movement

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

            # # Remove any None associations the new follower may have had
            # assoc_none = (
            #     session.query(UserToUserLink)
            #     .filter(
            #         UserToUserLink.movement_id == movement.id,
            #         UserToUserLink.follower_id == new_follower.id,
            #         UserToUserLink.leader_id.is_(None),
            #     )
            #     .group_by(UserToUserLink.follower_id)
            #     .all()
            # )
            # for a in assoc_none:
            #     a.destroy()


def remove_all_followers(leader_id: int, movement_id: int) -> None:
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
            poss_new_leaders = possible_leaders(user_to_user_link.follower, user_to_user_link.movement, session)
            poss_new_leaders = [l for l in poss_new_leaders if l.id != leader_id]
            # Add new UserToUserLinks for each former follower.
            if poss_new_leaders:
                new_leader = random.choice(poss_new_leaders)
                new_user_to_user_link = UserToUserLink(
                    movement, user_to_user_link.follower, new_leader
                )
                session.add(new_user_to_user_link)
            else:
                new_user_to_user_link = UserToUserLink(movement, user_to_user_link.follower, None)
                session.add(new_user_to_user_link)


def get_last_signal(
    leader_id: int, movement_id: int, session: Session
) -> Signal:
    """Find the last signal the leader has sent to the movement."""
    return (
        session.query(Signal)
        .filter_by(leader_id=leader_id, movement_id=movement_id)
        .order_by(desc("time_stamp"))
        .first()
    )


def send_signal(leader_id: int, movement_id: int, message: str = None):
    """Send signal as a leader in a movement, optionally with a message."""
    with session_scope() as session:
        leader = load_user(leader_id, session)
        movement = load_movement(movement_id, session)

        assert Subscription._subscription_exists(leader_id, movement_id, session)

        signal = Signal(leader, movement, message)
        session.add(signal)
        session.commit()


def possible_leaders(
    user: User, movement: Movement, session: Session
) -> Query:
    """Find possible leaders for a user in a movement."""

    leader_ids = session.query(UserToUserLink.leader_id).filter(
        UserToUserLink.movement_id == movement.id,
        not_(UserToUserLink.leader_id.is_(None)),
        UserToUserLink.follower_id == user.id,
        UserToUserLink.destroyed.is_(None)
    )

    possible_leaders = [user_to_user_link.follower for user_to_user_link in
        session.query(UserToUserLink)
        .filter(
            UserToUserLink.movement_id == movement.id,
            UserToUserLink.destroyed.is_(None),
            not_(UserToUserLink.follower_id == user.id)
        ).group_by(UserToUserLink.follower_id)
        .filter(not_(UserToUserLink.follower_id.in_(leader_ids)))
    ]
    
    # IDK why but if I don't add them to the session it crashes
    session.add_all(possible_leaders) 
    return possible_leaders