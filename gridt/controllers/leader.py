from .helpers import session_scope, load_movement, load_user, possible_followers, possible_leaders
from gridt.models import Signal
from gridt.models import MovementUserAssociation

from gridt.controllers.subscription import on_subscription, on_unsubscription

import random


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
        for new_follower in possible_followers(user, movement, session):
            mua = MovementUserAssociation(movement, new_follower, leader=user)
            session.add(mua)

            # Remove any None associations the new follower may have had
            assoc_none = (
                session.query(MovementUserAssociation)
                .filter(
                    MovementUserAssociation.movement_id == movement.id,
                    MovementUserAssociation.follower_id == new_follower.id,
                    MovementUserAssociation.leader_id.is_(None),
                )
                .group_by(MovementUserAssociation.follower_id)
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
        leader_muas_to_destroy = session.query(MovementUserAssociation).filter(
            MovementUserAssociation.movement_id == movement_id,
            MovementUserAssociation.destroyed.is_(None),
            MovementUserAssociation.leader_id == leader_id,
        ).all()

        for mua in leader_muas_to_destroy:
            mua.destroy()

        session.commit()

        # For each follower removed try to find a new leader
        for mua in leader_muas_to_destroy:
            poss_new_leaders = possible_leaders(mua.follower, mua.movement, session).all()
            poss_new_leaders = [l for l in poss_new_leaders if l.id != leader_id]
            # Add new MUAs for each former follower.
            if poss_new_leaders:
                new_leader = random.choice(poss_new_leaders)
                new_mua = MovementUserAssociation(
                    movement, mua.follower, new_leader
                )
                session.add(new_mua)
            else:
                new_mua = MovementUserAssociation(movement, mua.follower, None)
                session.add(new_mua)


# Add a listener to remove subscription event to remove all the followers for a leader.
on_unsubscription(_remove_all_followers)


def send_signal(leader_id: int, movement_id: int, message: str = None):
    """Send signal as a leader in a movement, optionally with a message."""
    with session_scope() as session:
        leader = load_user(leader_id, session)
        movement = load_movement(movement_id, session)

        assert leader in movement.active_users

        signal = Signal(leader, movement, message)
        session.add(signal)
        session.commit()
