from datetime import datetime
from sqlalchemy import Column, Integer, DateTime, ForeignKey, String
from sqlalchemy.orm import relationship

from gridt.db import Base

class MovementUserRelation(Base):
    """
    This class is an abstract representation of the relation between a user and movement.
    Class such as subscription and creation inherite from this class to provide their functionality.
    These classes exist to reduce coupling between users and movements.
    Aswell as, to adhere to the Open/Close Principle. 
    """
    __tablename__ = 'MovementUserRelation'
    id = Column(Integer, primary_key=True)

    # Define the type of relation between the user and the movement
    type = Column(String(20))
    __mapper_args__ = {
        "polymorphic_on": "type",
        "polymorphic_identity": "None"
    }

    # Keep track of when the relation was added and removed
    time_added = Column(DateTime(timezone=True))
    time_removed = Column(DateTime(timezone=True))

    # One way relation to the user through user_id column
    user_id = Column(Integer, ForeignKey('users.id'))
    user = relationship('User', foreign_keys=[user_id])

    # One way relation to the movement through movement_id column
    movement_id = Column(Integer, ForeignKey('movements.id'))
    movement = relationship('Movement', foreign_keys=[movement_id])

    def __init__(self, user=None, movement=None):
        """
        Initalization method for the relation between user and movement.

        Args:
            user (User, optional): The User related to the movement. Defaults to None.
            movement (Movement, optional): The Movement related to the user. Defaults to None.
        """
        self.user = user
        self.movement = movement
        self.time_added = datetime.now()

    def is_ended(self):
        """
        Check if the relation has ended

        Returns:
            bool: true if ended, otherwise false
        """
        return bool(self.time_removed)

    def end(self):
        """
        Ends the relation.

        Note:
            the relation is still present in the database
        """
        self.time_removed = datetime.now()