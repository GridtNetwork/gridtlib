import random
from sqlalchemy import desc
from .helpers import session_scope, possible_leaders
from gridt.models import User, Movement, MovementUserAssociation, Signal


def get_subscriptions(user_id: int) -> list:
    """Get list of movements that the user is subscribed to."""
    with session_scope() as session:
        user = session.query(User).get(user_id)
        current_movements = user.current_movements
        return [
            movement.dictify(user) for movement in current_movements
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
        leader = session.query(User).get(leader_id)
        follower = session.query(User).get(follower_id)
        movement = session.query(Movement).get(movement_id)

        # If there are no other possible leaders than we can't perform the
        # swap.
        poss_leaders = possible_leaders(follower, movement, session).all()
        if not poss_leaders:
            return None

        mua = session.query(MovementUserAssociation).filter(
            MovementUserAssociation.follower_id == follower.id,
            MovementUserAssociation.leader_id == leader.id,
            MovementUserAssociation.movement_id == movement.id,
            MovementUserAssociation.destroyed.is_(None),
        ).one()

        mua.destroy()

        new_leader = random.choice(poss_leaders)
        new_assoc = MovementUserAssociation(movement, follower, new_leader)
        session.add(new_assoc)

        leader_dict = new_leader.dictify()

        last_signal = session.query(Signal).filter_by(
            leader=new_leader,
            movement=movement
        ).order_by(desc("time_stamp")).first()

        if last_signal:
            time_stamp = str(last_signal.time_stamp)
            leader_dict["last_signal"] = time_stamp

        return leader_dict
