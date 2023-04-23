"""Model for user to user link in the database."""
from datetime import datetime
from sqlalchemy import Column, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from gridt.db import Base
from gridt.models import Movement, User


class UserToUserLink(Base):
    """
    UserToUserLink class for the edge between two users in a movement.

    This is an association class that lies at the foundation of the network.
    Think of this class as the arrows that connect followers with
    leaders within their respective circle of the movement.

    :param model.user.User follower: User that will be following.
    :param model.user.User leader: User that will lead.
    :param model.movement.Movement movement: Movement in which this
    relationship is happening.

    :attribute leader: The leading user.
    :attribute follower: The following user.
    :attribute movement: The movement in which this connection happens.
    """

    __tablename__ = "assoc"

    id = Column(Integer, primary_key=True)
    leader_id = Column(Integer, ForeignKey("users.id"))
    follower_id = Column(Integer, ForeignKey("users.id"))
    movement_id = Column(Integer, ForeignKey("movements.id"))
    created = Column(DateTime(timezone=True))
    destroyed = Column(DateTime(timezone=True))

    movement = relationship(Movement, foreign_keys=[movement_id])
    follower = relationship(User, foreign_keys=[follower_id])
    leader = relationship(User, foreign_keys=[leader_id])

    def __init__(
        self,
        movement: Movement = None,
        follower: User = None,
        leader: User = None
    ):
        """Construct a new user to user link."""
        self.follower = follower
        self.movement = movement
        self.leader = leader
        self.created = datetime.now()
        self.destroyed = None

    def __repr__(self):
        """Get the string representation of a user to user link."""
        graph_string = f"{self.follower_id}"
        if self.destroyed:
            graph_string += "X"
        if self.leader_id:
            graph_string += f"->{self.leader_id}"
        movement_id = self.movement_id
        return (
            f"<Association id={self.id} "
            f"movement={movement_id} "
            f"{graph_string} >"
        )

    def destroy(self):
        """
        Destroy this user to user link.

        Note: the Association can still be found in database.
        """
        self.destroyed = datetime.now()
