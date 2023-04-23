"""Gridt specific exceptions for the server developer to mald over."""


class UserNotFoundError(Exception):
    """Could not find a user in the database."""

    pass


class MovementNotFoundError(Exception):
    """Could not find a movement in the database."""

    pass


class SubscriptionNotFoundError(Exception):
    """Could not find a subscription between movement and user."""

    pass


class UserIsNotCreator(Exception):
    """Could not find a creation relation between movement and user."""

    pass


class AnnouncementNotFoundError(Exception):
    """Could not find an announcement in the database."""

    pass


class UserNotAdmin(Exception):
    """The user is not an administrator."""

    pass
