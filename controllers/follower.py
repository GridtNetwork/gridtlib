import random
from .helpers import session_scope, possible_leaders
from models import User, Movement, MovementUserAssociation


def get_subscriptions(user_id):
    with session_scope() as session:
        user = session.query(User).get(user_id)
        current_movements = set(user.current_movements)
        return [
            movement.dictify(user) for movement in current_movements
        ]


def swap_leader(follower_id, movement_id, leader_id):
    """
    Swap out the presented leader in the users leaders.

    :param follower_id: Id of the user who's leader will be swapped.
    :param movement_id: Movement in which the swap is supposed to happen
    :param leader_id: Id of the leader that will be swapped.
    :return: New leader or None
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

        return new_leader
