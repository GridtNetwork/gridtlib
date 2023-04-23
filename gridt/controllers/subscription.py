"""Controller for subscriptions."""
from gridt.models import Subscription
from gridt.controllers import follower as Follower, leader as Leader
from gridt.controllers import movements as Movements
from .helpers import (
    session_scope,
    load_movement,
    load_user,
    GridtExceptions
)

from sqlalchemy.orm.query import Query
from sqlalchemy.orm.session import Session


def _get_subscription(
    user_id: int, movement_id: int, session: Session
) -> Query:
    """
    Get a subscription helper.

    Args:
        user_id (int): The id of the user
        movement_id (int): The id of the movement
        session (Session): The session to communicate with the DB

    Returns:
        Query: A subscription query
    """
    subscriptions = (
        session.query(Subscription)
        .filter(
            Subscription.user_id == user_id,
            Subscription.movement_id == movement_id,
            Subscription.time_removed.is_(None)
        )
    )

    if not subscriptions.count():
        raise GridtExceptions.SubscriptionNotFoundError(
            f"User '{user_id}' is not subscribed to Movement '{movement_id}'.",
            " Or one or both do not exist"
        )

    return subscriptions.one()


def is_subscribed(user_id: int, movement_id: int) -> bool:
    """
    Check if a user is subscribed to a movement.

    Args:
        user_id (int): The id of the user
        movement_id (int): The id of the movement
    """
    with session_scope() as session:
        return _subscription_exists(user_id, movement_id, session)


def _subscription_exists(
    user_id: int, movement_id: int, session: Session
) -> bool:
    """
    Check if a subscription exists.

    Args:
        user_id (int): The id of the user
        movement_id (int): The id of the movement

    Returns:
        bool: True if the movement contains the user. otherwise, false
    """
    try:
        _get_subscription(user_id, movement_id, session)
    except GridtExceptions.SubscriptionNotFoundError:
        return False

    return True


def new_subscription(user_id: int, movement_id: int) -> dict:
    """
    Create a new subscription between a user and a movement.

    Args:
        user_id (int): The id of the user
        movement_id (int): The id of the movement

    Returns:
        dict: json of the new subscription
    """
    with session_scope() as session:
        user = load_user(user_id, session)
        movement = load_movement(movement_id, session)

        subscription = Subscription(user, movement)
        session.add(subscription)
        subscription_json = subscription.to_json()

    Follower.add_initial_leaders(user_id, movement_id)
    Leader.add_initial_followers(user_id, movement_id)

    return subscription_json


def remove_subscription(user_id: int, movement_id: int) -> dict:
    """
    End a subscription relation between a user and a movement.

    Args:
        user_id (int): The id of the user
        movement_id (int): The id of the movement

    Returns:
        dict: json of the removed subscription
    """
    with session_scope() as session:
        subscription = _get_subscription(user_id, movement_id, session)
        subscription.end()

        session.add(subscription)
        removed_json = subscription.to_json()

    Follower.remove_all_leaders(user_id, movement_id)
    Leader.remove_all_followers(user_id, movement_id)

    return removed_json


def get_subscribers(movement_id: int) -> list:
    """
    Get the all subscribers of a movement.

    Args:
        movement_id (int): The id of the movement

    Returns:
        list: List of all the users in json format.
    """
    with session_scope() as session:
        movement_subscribers = (
            session.query(Subscription)
            .filter(
                Subscription.movement_id == movement_id,
                Subscription.time_removed.is_(None)
            )
        )
        return [
            subscriber.user.to_json()
            for subscriber in movement_subscribers
        ]


def get_subscriptions(user_id: int) -> list:
    """
    Get all the subscriptions of a user.

    Args:
        user_id (int): The id of the user.

    Returns:
        list: List of all the movements in json format.
    """
    with session_scope() as session:
        user = load_user(user_id, session)
        user_subscriptions = (
            session.query(Subscription)
            .filter(
                Subscription.user_id == user_id,
                Subscription.time_removed.is_(None)
            )
        )
        return [
            Movements.extend_movement_json(
                movement=subscription.movement,
                user=user,
                session=session
            )
            for subscription in user_subscriptions
        ]


def add_json_subscription_details(json, movement, user, session) -> None:
    """
    Append subscription details to a dictionary.

    Args:
        json (dict): The json to append with the subscription details.
        movement (Movement): The movement the user is subscribed to.
        user (User): The user which is subscribed.
        session (Session): The session to use.
    """
    last_signal = Leader.get_last_signal(user.id, movement.id, session)
    json["last_signal_sent"] = (
        last_signal.to_json() if last_signal else None
    )

    json["leaders"] = []
    for leader in Follower.get_leaders(user, movement, session):
        leader_json = leader.to_json()

        last_leader_signal = Leader.get_last_signal(
            leader_id=leader.id,
            movement_id=movement.id,
            session=session
        )
        if last_leader_signal:
            leader_json.update(last_signal=last_leader_signal.to_json())

        json["leaders"].append(leader_json)
