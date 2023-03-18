"""Model for creation in the database."""
from .movement_user_relation import MovementUserRelation


class Creation(MovementUserRelation):
    """This class models the creation relation of a user to a movement."""

    __mapper_args__ = {
        "polymorphic_identity": "creation",
    }

    def __init__(self, user=None, movement=None):
        """
        Construct a new creation relation class.

        Args:
            user (User, optional): The user which create the movement.
            movement (Movement, optional): The movement the user created.
        """
        super().__init__(user, movement)

    def __repr__(self):
        """
        Get the string representation of the creation relation class.

        Returns:
            str: string representation of the object
        """
        return (
            f"<Creation relation: {self.user.username}"
            f" has created {self.movement.name}>"
        )

    def to_json(self) -> dict:
        """
        Get the json representation of a creation relation.

        Returns:
            dict: Json representation of the creation object
        """
        return {
            "movement": self.movement.to_json(),
            "user": self.user.to_json(),
            "time_started": str(self.time_added.astimezone()),
            "created": not self.has_ended()
        }
