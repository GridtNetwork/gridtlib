from sqlalchemy import desc
from .helpers import session_scope
from gridt.models import Signal, Movement, User


def send_signal(leader_id: int, movement_id: int, message: str = None):
    """Send signal as a leader in a movement, optionally with a message."""
    with session_scope() as session:
        leader = session.query(User).get(leader_id)
        movement = session.query(Movement).get(movement_id)

        assert leader in movement.active_users

        signal = Signal(leader, movement, message)
        session.add(signal)


def get_signal_history(user, movement, session, n):
    with session_scope() as session:
        return (
            session.query
            .filter_by(leader=user, movement=movement)
            .order_by(desc("time_stamp"))
            .limit(n)
            .all()
        )
