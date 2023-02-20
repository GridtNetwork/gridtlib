from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from gridt.db import Base
from gridt.models import Movement

class Announcement(Base):
    __tablename__ = "announcements"

    id = Column(Integer, primary_key=True)
    movement_id = Column(Integer, ForeignKey("movements.id"), nullable=False)
    message = Column(String(140), nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False)

    movement = relationship(Movement)

    def __init__(self, movement:Movement, message:str):
        """
        Constructors for movement announcements

        Args:
            movement (Movement): The movement to create an announcement for
            message (str): The message that the announcement should contain
        """
        self.movement = movement
        self.message = message
        self.timestamp = datetime.now()

    def __str__(self) -> str:
        """
        Stringify method for Announcements

        Returns:
            str: str representation of the Announcement
        """
        return f'Announcement for movement {self.movement.id}: {self.message}'
