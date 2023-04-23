"""Controller to retrieve network information."""

from .helpers import session_scope

from gridt.models import (
    UserToUserLink,
    Subscription,
    User,
)

from gridt.controllers.leader import get_last_signal

from sqlalchemy.orm.session import Session


def get_network_data(movement_id: int) -> dict:
    """
    Get network data from a movement.

    Args:
        movement_id (int): The id of the movement to retrieve the data for.

    Returns:
        dict: NetworkX compatible lists of edges and nodes as tuples.
    """
    with session_scope() as session:
        network_edges = __get_edges(movement_id=movement_id, session=session)
        network_nodes = __get_nodes(movement_id=movement_id, session=session)
    return dict(edges=network_edges, nodes=network_nodes)


def __get_edges(movement_id: int, session: Session) -> list:
    """Get the edges from a movement network."""
    links = session.query(UserToUserLink).filter(
        UserToUserLink.movement_id == movement_id,
        UserToUserLink.destroyed.is_(None)
    ).all()

    return [(link.follower.id, link.leader.id) for link in links]


def __get_nodes(movement_id: int, session: Session) -> list:
    """Get the nodes from a movement network."""
    users = session.query(User).join(Subscription).filter(
        Subscription.movement_id == movement_id,
        Subscription.time_removed.is_(None)
    ).all()

    return [__user_to_node(user, movement_id, session) for user in users]


def __user_to_node(
    user: User, movement_id: int, session: Session
) -> tuple:
    """Convert User to node data NetworkX can understand."""
    user_id = user.id
    signal = get_last_signal(user_id, movement_id, session)

    if not signal:
        return (user_id, None)

    node_data = signal.to_json()
    return (user_id, node_data)
