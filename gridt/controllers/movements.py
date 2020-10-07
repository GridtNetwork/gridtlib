import random
from itertools import chain
from .helpers import (
    session_scope,
    leaders,
    leaderless,
    possible_leaders,
    extend_movement_json,
    load_user,
    load_movement,
)
from gridt.models import Movement, MovementUserAssociation
from gridt.exc import MovementNotFoundError


def get_all_movements(user_id):
    """Get all movements."""
    with session_scope() as session:
        user = load_user(user_id, session)
        return [
            extend_movement_json(movement, user, session)
            for movement in session.query(Movement)
        ]


def get_movement(movement_identifier, user_id):
    """Get a movement."""
    with session_scope() as session:
        try:
            movement_identifier = int(movement_identifier)
            movement = load_movement(movement_identifier, session)
        except ValueError:
            movement = (
                session.query(Movement)
                .filter_by(name=movement_identifier)
                .one()
            )

        user = load_user(user_id, session)
        return extend_movement_json(movement, user, session)


def new_movement(
    user_id: int,
    name: str,
    interval: str,
    short_description: str = None,
    description: str = None,
):
    """Create a new movement."""
    with session_scope() as session:
        user = load_user(user_id, session)
        movement = Movement(name, interval, short_description, description)
        _subscribe(user, movement, session)
        session.add(movement)


def _subscribe(user, movement, session):
    """
    Add a user to the movement.

    The logic of this function is required by both "gridt.controllers.movement
    .new_movement" and "gridt.controllers.movement.subscribe", therefore the
    logic was extracted in this function.
    """
    while leaders(user, movement, session).count() < 4:
        pos_leaders = possible_leaders(user, movement, session).all()
        if pos_leaders:
            assoc = MovementUserAssociation(movement, user)
            assoc.leader = random.choice(pos_leaders)
            session.add(assoc)
        else:
            if leaders(user, movement, session).count() == 0:
                assoc = MovementUserAssociation(movement, user, None)
                session.add(assoc)
            break

    for new_follower in leaderless(user, movement, session):
        association = MovementUserAssociation(movement, new_follower, user)
        session.add(association)

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


def subscribe(user_id, movement_id):
    """Subscribe user to a movement."""
    with session_scope() as session:
        user = load_user(user_id, session)
        movement = load_movement(movement_id, session)

        _subscribe(user, movement, session)


def remove_user_from_movement(user_id: int, movement: int):
    with session_scope() as session:
        user = load_user(user_id, session)
        movement = load_movement(movement, session)

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


def movement_exists(movement_id):
    with session_scope() as session:
        try:
            load_movement(movement_id, session)
        except MovementNotFoundError:
            return False
        return True


def user_in_movement(user_id, movement_id):
    with session_scope() as session:
        user = load_user(user_id, session)
        movement = load_movement(movement_id, session)

        return user in movement.active_users
