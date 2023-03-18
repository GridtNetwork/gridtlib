"""Model for subscription in the database."""
from .movement_user_relation import MovementUserRelation


class Subscription(MovementUserRelation):
    """
    Subscription class for the subscription of a user to a movement.

    This class represents a table in the SQL database which holds rows of
    subscriptions. All the logic to edit an subscription can be found in this
    class.
    """

    __mapper_args__ = {
        "polymorphic_identity": "subscription",
    }

    def unsubscribe(self):
        """End the subscription."""
        self.end()

    def __init__(self, user=None, movement=None):
        """
        Construct a new subscription.

        Args:
            user (User, optional): The user which is subscribes to a movement.
            movement (Movement, optional): The movement the user is subscribed.
        """
        super().__init__(user, movement)

    def __repr__(self):
        """
        Get the string representation of the subscription.

        Returns:
            str: string representation of the object
        """
        return (
            f"<Subscription relation: {self.user.username}"
            f" is subscribed to {self.movement.name}>"
        )

    def to_json(self) -> dict:
        """
        Compute the json representation of the subscription.

        Returns:
            dict: Json representation of the subscription object.
        """
        return {
            "movement": self.movement.to_json(),
            "user": self.user.to_json(),
            "time_started": str(self.time_added.astimezone()),
            "subscribed": not self.has_ended()
        }
