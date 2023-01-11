import random
from sqlalchemy import desc
from sqlalchemy.orm.query import Query
from sqlalchemy import not_, func
from sqlalchemy.orm.session import Session

from .helpers import (
    session_scope,
    load_movement,
    load_user,
    leaders, 
)
from gridt.controllers.subscription import on_subscription, on_unsubscription, get_subscribers
from gridt.controllers import leader as Leader
from gridt.models import User, MovementToMovementLink, Signal, Movement

# Move variable to config
MESSAGE_HISTORY_MAX_DEPTH = 3


def _add_initial_leaders(follower_id: int, movement_id: int) -> None:
    """
    This function adds the initial leaders for a follower when the follower first joins the movement.

    Args:
        follower_id (int): The id of the follower in the movement
        movement_id (int): The id of the movement to get leaders from.
    """
    with session_scope() as session:
        user = load_user(follower_id, session)
        movement = load_movement(movement_id, session)

        while leaders(user, movement, session).count() < 4:
            avaiable = Leader.possible_leaders(user, movement, session).all()
            if avaiable:
                movement_to_movement_link = MovementToMovementLink(movement, user)
                movement_to_movement_link.leader = random.choice(avaiable)
                session.add(movement_to_movement_link)
            else:
                if leaders(user, movement, session).count() == 0:
                    # Case no leaders have been added, add None
                    movement_to_movement_link = MovementToMovementLink(movement, user, None)
                    session.add(movement_to_movement_link)
                break


# Add a listener to new subscription event to get the initial leaders
on_subscription(_add_initial_leaders)


def _remove_all_leaders(follower_id: int, movement_id: int) -> None:
    """
    This function removes all leaders from a follower when the follower leaves a movement.
    It then tries to find new followers for the leaders.

    Args:
        follower_id (int): The id of the follower in the movement.
        movement_id (int): The id of the movement itself.
    """
    with session_scope() as session:
        movement = load_movement(movement_id, session)

        follower_movement_to_movement_links_to_destroy = session.query(
            MovementToMovementLink
        ).filter(
            MovementToMovementLink.movement_id == movement_id,
            MovementToMovementLink.destroyed.is_(None),
            MovementToMovementLink.follower_id == follower_id,
        ).all()

        for movement_to_movement_link in follower_movement_to_movement_links_to_destroy:
            movement_to_movement_link.destroy()

        session.commit()

        # For each leader removed try to find a new follower
        for movement_to_movement_link in follower_movement_to_movement_links_to_destroy:
            if not movement_to_movement_link.leader:
                continue

            poss_followers = possible_followers(movement_to_movement_link.leader, movement_to_movement_link.movement, session).all()
            # Add new MovementToMovementLinks for each former leader.
            if poss_followers:
                new_follower = random.choice(poss_followers)
                new_movement_to_movement_link = MovementToMovementLink(
                    movement, new_follower, movement_to_movement_link.leader
                )
                session.add(new_movement_to_movement_link)


# Add a listener to remove subscription event to remove all the leaders of a follower.
on_unsubscription(_remove_all_leaders)


def get_leader(follower_id: int, movement_id: int, leader_id: int):
    """Get a leader for a follower in movement and list his history."""
    with session_scope() as session:
        leader = (
            session.query(User)
            .join(MovementToMovementLink.leader)
            .filter(
                MovementToMovementLink.follower_id == follower_id,
                MovementToMovementLink.movement_id == movement_id,
                MovementToMovementLink.leader_id == leader_id,
                MovementToMovementLink.destroyed.is_(None),
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
            .join(MovementToMovementLink.leader)
            .filter(
                MovementToMovementLink.follower_id == follower_id,
                MovementToMovementLink.movement_id == movement_id,
                MovementToMovementLink.leader_id == leader_id,
                MovementToMovementLink.destroyed.is_(None),
            )
            .one_or_none()
        )
        if leader:
            return True
        return False


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
        poss_leaders = Leader.possible_leaders(follower, movement, session).all()
        if not poss_leaders:
            return None

        movement_to_movement_link = (
            session.query(MovementToMovementLink)
            .filter(
                MovementToMovementLink.follower_id == follower.id,
                MovementToMovementLink.leader_id == leader.id,
                MovementToMovementLink.movement_id == movement.id,
                MovementToMovementLink.destroyed.is_(None),
            )
            .one()
        )

        movement_to_movement_link.destroy()

        new_leader = random.choice(poss_leaders)
        new_assoc = MovementToMovementLink(movement, follower, new_leader)
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

    :todo we should probably be using subscriptions here this is all very hacky
    """    

    follower_ids = session.query(MovementToMovementLink.follower_id).filter(
        MovementToMovementLink.movement_id == movement.id, MovementToMovementLink.leader_id == user.id, MovementToMovementLink.destroyed.is_(None)
    )

    valid_movement_to_movement_links = (
            session.query(
                MovementToMovementLink,
                func.count().label("movement_to_movement_link_count"),
            )
            .filter(
                MovementToMovementLink.movement_id == movement.id,
                MovementToMovementLink.destroyed.is_(None),
            )
            .group_by(MovementToMovementLink.follower_id)
            .subquery()
        )


    available_leaderless = (
        session
        .query(User)
        .join(User.follower_associations)
        .filter(
            valid_movement_to_movement_links.c.follower_id == User.id,
            valid_movement_to_movement_links.c.movement_to_movement_link_count < 4,
        )
        .group_by(MovementToMovementLink.follower_id).filter(
            not_(User.id == user.id), not_(User.id.in_(follower_ids))
        )
    )

    return available_leaderless
