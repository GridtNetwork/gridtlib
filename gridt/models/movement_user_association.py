from datetime import datetime
from sqlalchemy import Column, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from gridt.db import Base


class MovementUserAssociation(Base):
    """
    Association class that lies at the foundation of the network.
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

    movement = relationship("Movement", back_populates="user_associations")
    follower = relationship(
        "User",
        foreign_keys=[follower_id],
        back_populates="follower_associations",
    )
    leader = relationship("User", foreign_keys=[leader_id])

    def __init__(self, movement=None, follower=None, leader=None):
        # movement=None and follower=None
        # are required for correct functioning of
        # user_associations in ./movement.py
        self.follower = follower
        self.movement = movement
        self.leader = leader
        self.created = datetime.now()
        self.destroyed = None

    def __repr__(self):
        return f"<Association id={self.id} {self.follower}->{self.leader} in {self.movement}{'x' if self.destroyed else ''}>"

    def destroy(self):
        """
        Destroy this association.
        Association can still be found in database.
        """
        self.destroyed = datetime.now()
