from .movement_user_relation import MovementUserRelation

class Creation(MovementUserRelation):
    """
    This class models the creation relation of a user to a movement.
    """

    __mapper_args__ = {
        "polymorphic_identity": "creation",
    }

    def __init__(self, user=None, movement=None):
        """
        Constructor for the creation relation class 

        Args:
            user (User, optional): The user which create the movement. Defaults to None.
            movement (Movement, optional): The movement the user created. Defaults to None.
        """
        super().__init__(user, movement)

    def __repr__(self):
        """
        This method defines the string representation of the creation relation class

        Returns:
            str: string representation of the object
        """
        return f"<Creation relation: {self.user.username} has created {self.movement.name}>"
