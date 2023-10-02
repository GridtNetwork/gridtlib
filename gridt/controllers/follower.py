"""Controller for followers."""
import random
from operator import and_

from sqlalchemy import desc
from sqlalchemy import not_, func
from sqlalchemy.orm.session import Session

from .helpers import (
    session_scope,
    load_movement,
    load_user,
)

from gridt.controllers import leader as Leader
from gridt.models import User, UserToUserLink, Signal, Movement, Subscription

# Move variable to config
MESSAGE_HISTORY_MAX_DEPTH = 3


def add_initial_leaders(follower_id: int, movement_id: int) -> None:
    """
    Add the initial leaders for a follower upon joining a movement.

    Args:
        follower_id (int): The id of the follower in the movement
        movement_id (int): The id of the movement to get leaders from.
    """
    with session_scope() as session:
        user = load_user(follower_id, session)
        movement = load_movement(movement_id, session)

        while len(get_leaders(user, movement, session)) < 4:
            available = Leader.possible_leaders(user, movement, session)
            if not available:
                break

            random_leader = random.choice(available)
            user_to_user_link = UserToUserLink(movement, user, random_leader)
            session.add(user_to_user_link)


def remove_all_leaders(follower_id: int, movement_id: int) -> None:
    """
    Remove all leaders from a follower upon leaving a movement.

    Args:
        follower_id (int): The id of the follower in the movement.
        movement_id (int): The id of the movement itself.
    """
    with session_scope() as session:
        movement = load_movement(movement_id, session)

        follower_user_to_user_links_to_destroy = session.query(
            UserToUserLink
        ).filter(
            UserToUserLink.movement_id == movement_id,
            UserToUserLink.destroyed.is_(None),
            UserToUserLink.follower_id == follower_id,
        ).all()

        for user_to_user_link in follower_user_to_user_links_to_destroy:
            user_to_user_link.destroy()

        session.commit()

        # For each leader removed try to find a new follower
        for user_to_user_link in follower_user_to_user_links_to_destroy:
            if not user_to_user_link.leader:
                continue

            poss_followers = possible_followers(
                user=user_to_user_link.leader,
                movement=user_to_user_link.movement,
                session=session
            )
            # Add new UserToUserLinks for each former leader.
            if poss_followers:
                new_follower = random.choice(poss_followers)
                new_user_to_user_link = UserToUserLink(
                    movement, new_follower, user_to_user_link.leader
                )
                session.add(new_user_to_user_link)


def get_leaders(user: User, movement: Movement, session: Session) -> list:
    """
    Create a query for the leaders of a user in a movement from a session.

    :param gridt.models.user.User user: User that needs new leaders.
    :param list exclude: List of users (can be a user model or an id) to
    exclude from search.
    :returns: List object
    """
    return [
        user_to_user_link.leader
        for user_to_user_link in session.query(UserToUserLink).filter(
            UserToUserLink.follower_id == user.id,
            UserToUserLink.movement_id == movement.id,
            UserToUserLink.destroyed.is_(None)
        )
    ]


def get_leader(follower_id: int, movement_id: int, leader_id: int):
    """Get a leader for a follower in movement and list his history."""
    with session_scope() as session:
        leader_link = (
            session.query(UserToUserLink)
            .filter(
                UserToUserLink.follower_id == follower_id,
                UserToUserLink.movement_id == movement_id,
                UserToUserLink.leader_id == leader_id,
                UserToUserLink.destroyed.is_(None),
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
            session.query(UserToUserLink)
            .filter(
                UserToUserLink.follower_id == follower_id,
                UserToUserLink.movement_id == movement_id,
                UserToUserLink.leader_id == leader_id,
                UserToUserLink.destroyed.is_(None),
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

        user_to_user_link = (
            session.query(UserToUserLink)
            .filter(
                UserToUserLink.follower_id == follower.id,
                UserToUserLink.leader_id == leader.id,
                UserToUserLink.movement_id == movement.id,
                UserToUserLink.destroyed.is_(None),
            )
            .one()
        )

        user_to_user_link.destroy()

        new_leader = random.choice(poss_leaders)
        new_assoc = UserToUserLink(movement, follower, new_leader)
        session.add(new_assoc)

        leader_dict = new_leader.to_json()

        last_signal = (
            session.query(Signal)
            .filter_by(leader=new_leader, movement=movement)
            .order_by(desc("time_stamp"))
            .first()
        )

        if last_signal:
            leader_dict["last_signal"] = {
                "time_stamp": str(last_signal.time_stamp.astimezone()),
                "message": last_signal.message
            }

        return leader_dict


def possible_followers(
        user: User, movement: Movement, session: Session
) -> list:
    """
    Find possible followers for a user.

    Find the active users in this movement
    (movement.current_users) that have fewer than four leaders,
    excluding the current user or any of his followers.

    :param user User that would be the possible leader
    :param movement Movement where the leaderless are queried
    :param session Session in which the query is performed

    """
    SUB = Subscription

    follower_ids = session.query(UserToUserLink.follower_id).filter(
        UserToUserLink.movement_id == movement.id,
        UserToUserLink.leader_id == user.id,
        UserToUserLink.destroyed.is_(None)
    )

    potential_available_followers = (session.query(
        SUB,
        func.count(UserToUserLink.follower_id))
        .outerjoin(UserToUserLink, and_(
            SUB.user_id == UserToUserLink.follower_id,
            movement.id == UserToUserLink.movement_id)
        )
        .filter(
                SUB.movement_id == movement.id,
                not_(SUB.user_id == user.id),
                not_(SUB.user_id.in_(follower_ids)),
                UserToUserLink.destroyed.is_(None)
                )
        .group_by(SUB.user_id).all())

    return [
        subscription.user for subscription, counts
        in potential_available_followers if counts < 4
    ]
