from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from gridt.db import Base
from gridt.models import Movement, User

class Announcement(Base):
    __tablename__ = "announcements"

    id = Column(Integer, primary_key=True)
    movement_id = Column(Integer, ForeignKey("movements.id"), nullable=False)
    poster_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    message = Column(String(140), nullable=False)
    created_time = Column(DateTime(timezone=True), nullable=False)
    updated_time = Column(DateTime(timezone=True), nullable=True)
    removed_time = Column(DateTime(timezone=True), nullable=True)

    movement = relationship(Movement)
    poster = relationship(User)

    def __init__(self, movement:Movement, message:str, user:User):
        """
        Constructors for movement announcements

        Args:
            movement (Movement): The movement to create an announcement for
            message (str): The message that the announcement should contain
            user (User): The poster of the announcement
        """
        self.movement = movement
        self.message = message
        self.poster = user
        self.created_time = datetime.now()
        self.updated_time = None
        self.removed_time = None

    def __str__(self) -> str:
        """
        Stringify method for Announcements

        Returns:
            str: str representation of the Announcement
        """
        return f'Announcement for movement {self.movement.id}: {self.message}'

    def to_json(self) -> dict:
        """
        Converts the announcement to json

        Returns:
            dict: JSON representation of the Announcement
        """
        return {
            "id": self.id,
            "movement_id": self.movement_id,
            "poster": self.poster.to_json(),
            "message": self.message,
            "created_time": self.created_time,
            "updated_time": self.updated_time
        }

    def update_message(self, message: str):
        """
        Updates the message of the announcement

        Args:
            message (str): The message that should replace the previous announcement
        """
        self.message = message
        self.updated_time = datetime.now()

    def remove(self):
        """
        Delete the announcement
        """
        self.removed_time = datetime.now()
