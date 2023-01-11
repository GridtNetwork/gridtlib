from gridt.models import Subscription
import gridt.exc as E 
from .helpers import (
    session_scope,
    load_movement,
    load_user,
    extend_movement_json,
)

from sqlalchemy.orm.query import Query
from sqlalchemy.orm.session import Session

import types

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


# set of events to listening to the subscription of a user to a movement
_on_subscription_events = set()


def on_subscription(event_func: types.FunctionType) -> None:
    """
    This function adds an eventlistener to the function new_subscription

    Args:
        event_func (types.FunctionType): A function that should be called whenever a new subscription is made.
        The function should be in the type (user_id: int, movement_id: int) -> None.
    """
    _on_subscription_events.add(event_func)


def _notify_subsciption_listeners(user_id: int, movement_id: int) -> None:
    """
    This helper function calls all event functions for each listener.

    Args:
        user_id (int): The id of the user who just subscribed.
        movement_id (int): The id of the movement the user subscribed to.
    """
    for event in _on_subscription_events:
        event(user_id, movement_id)


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

    # Emit message to all listeners
    _notify_subsciption_listeners(user_id, movement_id)

    return subscription_json


# set of events listening to the unsubscription of a user to a movement
_on_unsubscription_events = set()


def on_unsubscription(event_func: types.FunctionType) -> None:
    """
    This function adds an event listener to the function remove subscription

    Args:
        event_func (types.FunctionType): A function that should be called whenever a subscriptions is ended.
        The function should be in the type (user_id: int, movement_id: int) -> None
    """
    _on_unsubscription_events.add(event_func)


def _notify_remove_subscription_listeners(user_id: int, movement_id: int):
    """
    This helper function calls all notify functions for each listener.

    Args:
        user_id (int): The id of the user who subscription to the movement was removed.
        movement_id (int): The id of the movement who relation to the user was removed.
    """
    for event in _on_unsubscription_events:
        event(user_id, movement_id)


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

    # Emit event to listeners
    _notify_remove_subscription_listeners(user_id, movement_id)

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

