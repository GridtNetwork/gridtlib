from datetime import datetime
from sqlalchemy import Column, Integer, ForeignKey, DateTime, String
from sqlalchemy.orm import relationship
from gridt.db import Base


class Signal(Base):
    """
    Representation of signals in the database.

    :attribute leader: The leader that created this signal.
    :attribute movement: The movement that this signal was created in.
    :attribute message: Message from the leader.
    """

    __tablename__ = "signals"
    id = Column(Integer, primary_key=True)
    leader_id = Column(Integer, ForeignKey("users.id"))
    movement_id = Column(Integer, ForeignKey("movements.id"))
    time_stamp = Column(DateTime(timezone=True), nullable=False)
    message = Column(String(140))

    leader = relationship("User")
    movement = relationship("Movement")

    def __init__(self, leader, movement, message=None):
        self.leader = leader
        self.movement = movement
        self.time_stamp = datetime.now()
        self.message = message

    def to_json(self):
        signal_dict = {
            "time_stamp": str(self.time_stamp.astimezone()),
        }

        if self.message:
            signal_dict["message"] = self.message

        return signal_dict
