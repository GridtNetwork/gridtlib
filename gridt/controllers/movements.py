import random
from itertools import chain
from .helpers import session_scope, leaders, leaderless, possible_leaders
from gridt.models import Movement, User, MovementUserAssociation


def all_movements():
    with session_scope() as session:
        return session.query(Movement).all()


def new_movement(
    user_id, name, interval, short_description=None, description=None
):
    with session_scope() as session:
        user = session.query(User).get(user_id)
        movement = Movement(name, interval, short_description, description)
        movement.add_user(user)
        session.add(movement)


def get_movement(identifier):
    with session_scope() as session:
        try:
            identifier = int(identifier)
            movement = session.query(Movement).get(identifier)
        except ValueError:
            movement = Movement.filter_by(name=identifier).one()

        return movement.dictify()


def subscribe(user_id, movement_id):
    with session_scope() as session:
        user = session.query(User).get(user_id)
        movement = session.query(Movement).get(movement_id)

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


def remove_user_from_movement(user_id: int, movement: int):
    with session_scope() as session:
        user = session.query(User).get(user_id)
        movement = session.query(Movement).get(movement)

        leader_muas_to_destroy = (
            session.query(MovementUserAssociation)
            .filter(
                MovementUserAssociation.movement_id == movement.id,
                MovementUserAssociation.destroyed.is_(None),
                MovementUserAssociation.leader_id == user.id,
            )
        )

        follower_muas_to_destroy = (
            session.query(MovementUserAssociation)
            .filter(
                MovementUserAssociation.movement_id == movement.id,
                MovementUserAssociation.destroyed.is_(None),
                MovementUserAssociation.follower_id == user.id,
            )
        )

        for mua in set(chain(follower_muas_to_destroy, leader_muas_to_destroy)):
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
