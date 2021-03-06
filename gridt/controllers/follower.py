import random
from sqlalchemy import desc
from .helpers import (
    session_scope,
    possible_leaders,
    extend_movement_json,
    load_movement,
    load_user,
)
from gridt.models import User, MovementUserAssociation, Signal

# Move variable to config
MESSAGE_HISTORY_MAX_DEPTH = 3


def get_leader(follower_id: int, movement_id: int, leader_id: int):
    """Get a leader for a follower in movement and list his history."""
    with session_scope() as session:
        leader = (
            session.query(User)
            .join(MovementUserAssociation.leader)
            .filter(
                MovementUserAssociation.follower_id == follower_id,
                MovementUserAssociation.movement_id == movement_id,
                MovementUserAssociation.leader_id == leader_id,
                MovementUserAssociation.destroyed.is_(None),
            )
            .one()
        )

        resp = leader.to_json()
        history = (
            session.query(Signal)
            .filter_by(leader_id=leader_id, movement_id=movement_id)
            .order_by(desc("time_stamp"))
            .limit(MESSAGE_HISTORY_MAX_DEPTH)
            .all()
        )
        resp["message_history"] = [signal.to_json() for signal in history]

        return resp


def follows_leader(follower_id: int, movement_id: int, leader_id: int):
    """Check if follower is following leader in movement."""
    with session_scope() as session:
        leader = (
            session.query(User)
            .join(MovementUserAssociation.leader)
            .filter(
                MovementUserAssociation.follower_id == follower_id,
                MovementUserAssociation.movement_id == movement_id,
                MovementUserAssociation.leader_id == leader_id,
                MovementUserAssociation.destroyed.is_(None),
            )
            .one_or_none()
        )
        if leader:
            return True
        return False


def get_subscriptions(user_id: int) -> list:
    """Get list of movements that the user is subscribed to."""
    with session_scope() as session:
        user = load_user(user_id, session)
        return [
            extend_movement_json(movement, user, session)
            for movement in user.current_movements
        ]


def swap_leader(follower_id: int, movement_id: int, leader_id: int) -> dict:
    """
    Swap out the presented leader in the users leaders.

    :param follower_id: Id of the user who's leader will be swapped.
    :param movement_id: Movement in which the swap is supposed to happen
    :param leader_id: Id of the leader that will be swapped.
    :return: New leader dictionary or None
    """
    with session_scope() as session:
        leader = load_user(leader_id, session)
        follower = load_user(follower_id, session)
        movement = load_movement(movement_id, session)

        # If there are no other possible leaders than we can't perform the
        # swap.
        poss_leaders = possible_leaders(follower, movement, session).all()
        if not poss_leaders:
            return None

        mua = (
            session.query(MovementUserAssociation)
            .filter(
                MovementUserAssociation.follower_id == follower.id,
                MovementUserAssociation.leader_id == leader.id,
                MovementUserAssociation.movement_id == movement.id,
                MovementUserAssociation.destroyed.is_(None),
            )
            .one()
        )

        mua.destroy()

        new_leader = random.choice(poss_leaders)
        new_assoc = MovementUserAssociation(movement, follower, new_leader)
        session.add(new_assoc)

        leader_dict = new_leader.to_json()

        last_signal = (
            session.query(Signal)
            .filter_by(leader=new_leader, movement=movement)
            .order_by(desc("time_stamp"))
            .first()
        )

        if last_signal:
            time_stamp = str(last_signal.time_stamp)
            leader_dict["last_signal"] = time_stamp

        return leader_dict
