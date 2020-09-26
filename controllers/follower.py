from .helpers import session_scope
from models import User


def get_subscriptions(user_id):
    with session_scope() as session:
        user = session.query(User).get(user_id)
        current_movements = set(user.current_movements)
        return [
            movement.dictify(user) for movement in current_movements
        ]
