from .helpers import session_scope
from models import User
import jwt
from util.email_templates import (
    send_password_reset_email,
    send_password_change_notification,
)


def update_user_bio(user_id: int, bio: str):
    with session_scope() as session:
        user = session.query(User).get(user_id)
        user.bio = bio


def change_password(user_id: int, new_password: str):
    with session_scope() as session:
        user = session.query(User).get(user_id)
        user.hash_and_store_password(new_password)
        send_password_change_notification(user.email)


def change_email(user_id: int, new_email: str):
    with session_scope() as session:
        user = session.query(User).get(user_id)
        user.email = new_email


def request_password_reset(email: int, secret_key: str):
    """
    Make a dictionary containing the e-mail for password reset
    + an expiration timestamp such that the token is valid for 2 hours
    and encodes it into a JWT.
    """
    with session_scope() as session:
        user = session.query(User).filter_by(email=email).one()

        token = user.get_password_reset_token(secret_key)
        send_password_reset_email(user.email, token)


def reset_password(token: str, password: str, secret_key: str):
    with session_scope() as session:
        payload = jwt.decode(token, secret_key, algorithms=["HS256"])
        user = session.query(User).get(payload["user_id"])
        user.hash_and_store_password(password)
        send_password_change_notification(user.email)


def verify_password(id: int, password: str):
    with session_scope() as session:
        user = session.query(User).get(id)
        return user.verify_password(password)


def register(username: str, email: str, password: str):
    with session_scope() as session:
        user = User(username, email, password)
        session.add(user)


def get_identity(user_id: int):
    with session_scope() as session:
        user = session.query(User).get(user_id)
        return user.dictify(include_email=True)
