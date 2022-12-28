from gridt.models import Subscription
from sqlalchemy.orm.query import Query
from gridt.db import Session
from .helpers import (
    session_scope,
    load_movement,
    load_user,
    extend_movement_json,
)


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
    return (
        session.query(Subscription)
        .filter_by(
            Subscription.user_id == user_id,
            Subscription.movement_id == movement_id,
            Subscription.time_removed.is_(None)
        )
        .one()
    )


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
        except:
            return False

    return True


def new_subscribtion(user_id: int, movement_id: int) -> dict:
    """
    Creates a new subscription between a user and a movement.

    Args:
        user_id (int): The id of the user
        movement_id (int): The id of the movement

    Returns:
        dict: json of the new subscription
    """
    with session_scope() as session:
        user = load_user(user_id)
        movement = load_movement(movement_id)
        
        subscription = Subscription(user, movement)
        session.add(subscription)


        # TODO: This should be handeled by an event listener in the follower controller
        # We emit an event here that the subscription added
        # I add the imports here so I don't forget to remove them when I refactor this
        import random
        from gridt.models import MovementUserAssociation
        from .helpers import (
            leaders, 
            possible_leaders,
            possible_followers
        )
        
        # Give that new subscriber other leaders to follow in the movement
        while leaders(user, movement, session).count() < 4:
            avaiable = possible_leaders(user, movement, session).all()
            if avaiable:
                mua = MovementUserAssociation(movement, user)
                mua.leader = random.choice(avaiable)
                session.add(mua)
            else:
                if leaders(user, movement, session).count() == 0:
                    # Case no leaders have been added, add None
                    mua = MovementUserAssociation(movement, user, None)
                    session.add(mua)
                break

        # Give that new subscriber other followers to follow in the movement
        for new_follower in possible_followers(user, movement, session):
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

    return subscription.to_json()


def remove_subscribtion(user_id: int, movement_id: int) -> dict:
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


        # TODO: Again, this should be handled by emitting an event
        # I add the imports here so I don't forget to remove them when I refactor this
        from gridt.models import MovementUserAssociation
        from itertools import chain
        import random
        from .helpers import (
            possible_leaders,
            possible_followers
        )

        user, movement = subscription.user, subscription.movement

        # Remove all links to the removed subscriber
        leader_muas_to_destroy = session.query(MovementUserAssociation).filter(
            MovementUserAssociation.movement_id == movement.id,
            MovementUserAssociation.destroyed.is_(None),
            MovementUserAssociation.leader_id == user.id,
        )

        follower_muas_to_destroy = session.query(
            MovementUserAssociation
        ).filter(
            MovementUserAssociation.movement_id == movement.id,
            MovementUserAssociation.destroyed.is_(None),
            MovementUserAssociation.follower_id == user.id,
        )

        for mua in set(
            chain(follower_muas_to_destroy, leader_muas_to_destroy)
        ):
            mua.destroy()

        session.commit()

        # Add new links to followers without links
        for mua in leader_muas_to_destroy:
            poss_leaders = possible_leaders(mua.follower)
            # Add new MUAs for each former follower.
            if possible_leaders:
                new_leader = random.choice(poss_leaders)
                new_mua = MovementUserAssociation(
                    movement, mua.follower, new_leader
                )
                session.add(new_mua)
            else:
                new_mua = MovementUserAssociation(movement, mua.follower, None)
                session.add(new_mua)

    return subscription.to_json()


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
            .filter_by(
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
            .filter_by(
                Subscription.user_id == user_id,
                Subscription.time_removed.is_(None)
            )
        )
        return [
            extend_movement_json(subscription.movement, user, session)
            for subscription in user_subscriptions
        ]

