import random
from sqlalchemy import desc
from sqlalchemy.orm.query import Query
from sqlalchemy import not_, func
from sqlalchemy.orm.session import Session

from .helpers import (
    session_scope,
    load_movement,
    load_user, 
)

from gridt.controllers import leader as Leader
from gridt.models import User, MovementUserAssociation, Signal, Movement

# Move variable to config
MESSAGE_HISTORY_MAX_DEPTH = 3


def add_initial_leaders(follower_id: int, movement_id: int) -> None:
    """
    This function adds the initial leaders for a follower when the follower first joins the movement.

    Args:
        follower_id (int): The id of the follower in the movement
        movement_id (int): The id of the movement to get leaders from.
    """
    with session_scope() as session:
        user = load_user(follower_id, session)
        movement = load_movement(movement_id, session)

        while len(get_leaders(user, movement, session)) < 4:
            avaiable = Leader.possible_leaders(user, movement, session)
            if avaiable:
                mua = MovementUserAssociation(movement, user)
                mua.leader = random.choice(avaiable)
                session.add(mua)
            else:
                if not get_leaders(user, movement, session):
                    # Case no leaders have been added, add None
                    mua = MovementUserAssociation(movement, user, None)
                    session.add(mua)
                break


def remove_all_leaders(follower_id: int, movement_id: int) -> None:
    """
    This function removes all leaders from a follower when the follower leaves a movement.
    It then tries to find new followers for the leaders.

    Args:
        follower_id (int): The id of the follower in the movement.
        movement_id (int): The id of the movement itself.
    """
    with session_scope() as session:
        movement = load_movement(movement_id, session)

        follower_muas_to_destroy = session.query(
            MovementUserAssociation
        ).filter(
            MovementUserAssociation.movement_id == movement_id,
            MovementUserAssociation.destroyed.is_(None),
            MovementUserAssociation.follower_id == follower_id,
        ).all()

        for mua in follower_muas_to_destroy:
            mua.destroy()

        session.commit()

        # For each leader removed try to find a new follower
        for mua in follower_muas_to_destroy:
            if not mua.leader:
                continue

            poss_followers = possible_followers(mua.leader, mua.movement, session)
            # Add new MUAs for each former leader.
            if poss_followers:
                new_follower = random.choice(poss_followers)
                new_mua = MovementUserAssociation(
                    movement, new_follower, mua.leader
                )
                session.add(new_mua)


def get_leaders(user: User, movement: Movement, session: Session) -> list:
    """
    Create a query for the leaders of a user in a movement from a session.

    :param gridt.models.user.User user: User that needs new leaders.
    :param list exclude: List of users (can be a user model or an id) to
    exclude from search.
    :returns: List object
    """
    return [ mua.leader for mua in
        session.query(MovementUserAssociation)
        .filter(
            MovementUserAssociation.follower_id == user.id,
            MovementUserAssociation.movement_id == movement.id,
            not_(MovementUserAssociation.leader_id.is_(None)),
            MovementUserAssociation.destroyed.is_(None)
        )
    ]


def get_leader(follower_id: int, movement_id: int, leader_id: int):
    """Get a leader for a follower in movement and list his history."""
    with session_scope() as session:
        leader_link = (
            session.query(MovementUserAssociation)
            .filter(
                MovementUserAssociation.follower_id == follower_id,
                MovementUserAssociation.movement_id == movement_id,
                MovementUserAssociation.leader_id == leader_id,
                MovementUserAssociation.destroyed.is_(None),
            )
            .one()
        )

        resp = leader_link.leader.to_json()
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
            session.query(MovementUserAssociation)
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
        poss_leaders = Leader.possible_leaders(follower, movement, session)
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
    MUA = MovementUserAssociation

    follower_ids = session.query(MUA.follower_id).filter(
        MUA.movement_id == movement.id, MUA.leader_id == user.id, MUA.destroyed.is_(None)
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


    available_leaderless = (
        session
        .query(MUA)
        .filter(
            valid_muas.c.follower_id == MUA.follower_id,
            valid_muas.c.mua_count < 4,
        )
        .group_by(MUA.follower_id).filter(
            not_(MUA.follower_id == user.id), not_(MUA.follower_id.in_(follower_ids))
        )
    )

    return [mua.follower for mua in available_leaderless]
