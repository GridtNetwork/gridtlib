from sqlalchemy import Column, Integer, String, or_, func
from sqlalchemy.orm import relationship, object_session
from sqlalchemy.ext.associationproxy import association_proxy

from gridt.db import Base
from .signal import Signal
from .movement_user_association import MovementUserAssociation
from .user import User


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

    def __init__(self, name, interval, short_description="", description=""):
        self.name = name
        self.interval = interval
        self.short_description = short_description
        self.description = description

    @property
    def active_users(self):
        return (
            object_session(self)
            .query(User)
            .join(Movement.user_associations)
            .filter(
                or_(
                    MovementUserAssociation.leader_id == User.id,
                    MovementUserAssociation.follower_id == User.id,
                ),
                MovementUserAssociation.movement_id == self.id,
                MovementUserAssociation.destroyed.is_(None),
            )
            .group_by(User.id)
        )

    @property
    def leaderless(self):
        session = object_session(self)

        MUA = MovementUserAssociation

        valid_muas = (
            session.query(
                MUA,
                func.count().label("mua_count"),
            )
            .filter(
                MUA.movement_id == self.id,
                MUA.destroyed.is_(None),
            )
            .group_by(MUA.follower_id)
            .subquery()
        )

        return (
            session
            .query(User)
            .join(User.follower_associations)
            .filter(
                valid_muas.c.follower_id == User.id,
                valid_muas.c.mua_count < 4,
            )
            .group_by(MUA.follower_id)
        )

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
