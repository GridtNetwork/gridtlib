import random
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.ext.associationproxy import association_proxy

from db import Base
from .user import User
from .signal import Signal
from .movement_user_association import MovementUserAssociation


class Movement(Base):
    """
    Intuitive representation of movements in the database. ::

        flossing = Movement('flossing', 'daily')
        robin = User.find_by_id(1)
        pieter = User.find_by_id(2)
        jorn = User.find_by_id(3)
        flossing.users = [robin, pieter, jorn]
        flossing.save_to_db()

    :Note: changes are only saved to the database when
        :func:`Movement.save_to_db` is called.

    :param str name: Name of the movement
    :param str interval: Interval in which the user is supposed to repeat the
    action.
    :param str short_description: Give a short description for your movement.
    :attribute str description: More elaborate description of your movement.
    :attribute users: All user that have been subscribed to this movement.
    :attribute user_associations: All instances of UserAssociation that point
    to this movement
    :class:`models.movement_user_association.MovementUserAssociation` with that
    link to this movement.
    """

    __tablename__ = "movements"

    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    interval = Column(String(20), nullable=False)
    short_description = Column(String(100))
    description = Column(String(1000))

    user_associations = relationship(
        "MovementUserAssociation",
        back_populates="movement",
        cascade="all, delete-orphan",
    )

    users = association_proxy(
        "user_associations",
        "follower",
        creator=lambda user: MovementUserAssociation(follower=user),
    )

    @property
    def current_users(self):
        return (
            User.query.join(User.follower_associations)
            .filter(
                MovementUserAssociation.movement_id == self.id,
                MovementUserAssociation.destroyed is None,
            )
            .group_by(User.id)
            .all()
        )

    def __init__(self, name, interval, short_description="", description=""):
        self.name = name
        self.interval = interval
        self.short_description = short_description
        self.description = description

    def swap_leader(self, user, leader):
        """
        Swap out the presented leader in the users leaders.

        :param user: User who's leader will be swapped.
        :param leader: The leader that will be swapped.
        :return: New leader or None
        """
        if not leader:
            raise ValueError("Cannot swap a leader that does not exist.")

        # We can not change someone's leader if they are not already
        # following that leader.
        if leader and leader not in user.leaders(self):
            raise ValueError("User is not following that leader.")

        # If there are no other possible leaders than we can't perform the
        # swap.
        possible_leaders = self.find_leaders(user)
        if not possible_leaders:
            return None

        mua = MovementUserAssociation.query.filter(
            MovementUserAssociation.follower_id == user.id,
            MovementUserAssociation.leader_id == leader.id,
            MovementUserAssociation.movement_id == self.id,
            MovementUserAssociation.destroyed is None,
        ).one()

        mua.destroy()

        new_leader = random.choice(possible_leaders)
        new_assoc = MovementUserAssociation(self, user, new_leader)

        new_assoc.save_to_db()

        return new_leader

    def dictify(self, user):
        """
        Return a dict version of this movement, ready for shipping to JSON.

        :param user: The user that requests the information.
        """
        movement_dict = {
            "name": self.name,
            "id": self.id,
            "short_description": self.short_description,
            "description": self.description,
            "interval": self.interval,
        }

        movement_dict["subscribed"] = False
        if user in self.current_users:
            movement_dict["subscribed"] = True

            last_signal = Signal.find_last(user, self)
            movement_dict["last_signal_sent"] = (
                {"time_stamp": str(last_signal.time_stamp.astimezone())}
                if last_signal
                else None
            )

            # Extend the user dictionary with the last signal
            movement_dict["leaders"] = [
                dict(
                    leader.dictify(),
                    **(
                        {
                            "last_signal": Signal.find_last(
                                leader, self
                            ).dictify()
                        }
                        if Signal.find_last(leader, self)
                        else {}
                    ),
                )
                for leader in user.leaders(self)
            ]

        return movement_dict

    def __repr__(self):
        return f"<Movement name={self.name}>"
