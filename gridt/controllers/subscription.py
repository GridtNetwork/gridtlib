from gridt.models import Subscription
from gridt.controllers import follower as Follower, leader as Leader
import gridt.exc as E 
from .helpers import (
    session_scope,
    load_movement,
    load_user,
    extend_movement_json,
)

from sqlalchemy.orm.query import Query
from sqlalchemy.orm.session import Session


def _get_subscription(user_id: int, movement_id: int, session: Session) -> Query:
    """
    Helper function to get subscription

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
        raise E.SubscriptionNotFoundError(f"User '{user_id}' is not subscribed to Movement '{movement_id}'. Or one or both do not exist")
    
    return subscriptions.one()


def is_subscribed(user_id: int, movement_id: int) -> bool:
    """
    Checks if a user is subscribled to a movement

    Args:
        user_id (int): The id of the user
        movement_id (int): The id of the movement

    Returns:
        bool: True if the movement contains the user. otherwise, false
    """
    with session_scope() as session:
        try: 
            _get_subscription(user_id, movement_id, session)
        except E.SubscriptionNotFoundError:
            return False

    return True


def new_subscription(user_id: int, movement_id: int) -> dict:
    """
    Creates a new subscription between a user and a movement.

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
    Ends a subscription relation between a user and a movement.

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
    Gets the all subscribers of a movement.

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
        return [subscriber.user.to_json() for subscriber in movement_subscribers]


def get_subscriptions(user_id: int) -> list:
    """
    Gets all the subscriptions of a user.

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
            extend_movement_json(subscription.movement, user, session)
            for subscription in user_subscriptions
        ]

