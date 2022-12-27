from .movement_user_relation import MovementUserRelation

class Subscription(MovementUserRelation):
    """
    This class models the subscription of a user to a movement.
    """

    __mapper_args__ = {
        "polymorphic_identity": "subscription",
    }

    def unsubscribe(self):
        """
        Ends the subscription.
        """
        self.end()

    def __init__(self, user=None, movement=None):
        """
        Constructor for the subscription class 

        Args:
            user (User, optional): The user which is subscribes to a movement. Defaults to None.
            movement (Movement, optional): The movement the user is subscribing to. Defaults to None.
        """
        super().__init__(user, movement)

    def __repr__(self):
        """
        This method defines the string representation of the class

        Returns:
            str: string representation of the object
        """
        return f"<Subscription relation: {self.user.username} is subscribed to {self.movement.name}>"
