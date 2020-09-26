from datetime import datetime
from .helpers import session_scope
from models import User
import jwt
from util.email_templates import (
    send_password_reset_email,
    send_password_change_notification,
)


def update_user_bio(user_id, bio):
    with session_scope() as session:
        user = session.query(User).get(user_id)
        user.bio = bio


def change_password(user_id, new_password):
    with session_scope() as session:
        user = session.query(User).get(user_id)
        user.hash_and_store_password(new_password)
        send_password_change_notification(user.email)


def change_email(user_id, new_email):
    with session_scope() as session:
        user = session.query(User).get(user_id)
        user.email = new_email


def request_password_reset(email, secret_key):
    """
    Make a dictionary containing the e-mail for password reset
    + an expiration timestamp such that the token is valid for 2 hours
    and encodes it into a JWT.
    """
    with session_scope() as session:
        user = session.query(User).filter_by(email=email).one()

        now = datetime.datetime.now()
        valid = datetime.timedelta(hours=2)
        exp = now + valid
        exp = exp.timestamp()

        payload = {"user_id": user.id, "exp": exp}

        token = jwt.encode(payload, secret_key, algorithm="HS256").decode(
            "utf-8"
        )
        send_password_reset_email(user.email, token)


def reset_password(token, password, secret_key):
    with session_scope() as session:
        payload = jwt.decode(token, secret_key, algorithms=["HS256"])
        user = session.query(User).get(payload["user_id"])
        user.hash_and_store_password(password)
        send_password_change_notification(user.email)


def verify_password(id, password):
    with session_scope() as session:
        user = session.query(User).get(id)
        return user.verify_password(password)


def register(username, email, password):
    with session_scope() as session:
        user = User(username, email, password)
        session.add(user)


def get_identity(user_id):
    with session_scope() as session:
        user = session.query(User).get(user_id)
        return user.dictify(include_email=True)
