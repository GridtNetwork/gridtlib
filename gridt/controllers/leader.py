from .helpers import session_scope, load_movement, load_user
from gridt.models import Signal


def send_signal(leader_id: int, movement_id: int, message: str = None):
    """Send signal as a leader in a movement, optionally with a message."""
    with session_scope() as session:
        leader = load_user(leader_id, session)
        movement = load_movement(movement_id, session)

        assert leader in movement.active_users

        signal = Signal(leader, movement, message)
        session.add(signal)
        session.commit()
