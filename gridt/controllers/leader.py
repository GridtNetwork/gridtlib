from .helpers import session_scope, load_movement, load_user, leaders
from gridt.models import Signal, User, Movement
from gridt.models import MovementUserAssociation

from gridt.controllers.subscription import on_subscription, on_unsubscription, is_subscribed
from gridt.controllers import follower as Follower
from gridt.controllers import subscription as Subscription

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
            poss_new_leaders = possible_leaders(mua.follower, mua.movement, session)
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

        assert is_subscribed(leader_id, movement_id)

        signal = Signal(leader, movement, message)
        session.add(signal)
        session.commit()


def possible_leaders(
    user: User, movement: Movement, session: Session
) -> Query:
    """Find possible leaders for a user in a movement."""
    MUA = MovementUserAssociation

    leader_ids = session.query(MUA.leader_id).filter(
        MUA.movement_id == movement.id,
        not_(MUA.leader_id.is_(None)),
        MUA.follower_id == user.id,
        MUA.destroyed.is_(None)
    )

    possible_leaders = [mua.follower for mua in
        session.query(MUA)
        .filter(
            MUA.movement_id == movement.id,
            MUA.destroyed.is_(None),
            not_(MUA.follower_id == user.id)
        ).group_by(MUA.follower_id)
        .filter(not_(MUA.follower_id.in_(leader_ids)))
    ]
    
    # IDK why but if I don't add them to the session it crashes
    session.add_all(possible_leaders) 
    return possible_leaders
