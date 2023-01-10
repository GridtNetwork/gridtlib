from sqlalchemy import Column, Integer, String

from gridt.db import Base


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

    def __init__(self, name, interval, short_description="", description=""):
        self.name = name
        self.interval = interval
        self.short_description = short_description
        self.description = description

    def to_json(self):
        """Jsonify this movement."""
        return {
            "name": self.name,
            "id": self.id,
            "short_description": self.short_description,
            "description": self.description,
            "interval": self.interval,
        }

    def __repr__(self):
        return f"<Movement name={self.name}>"
