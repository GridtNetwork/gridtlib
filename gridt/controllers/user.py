import jwt
from .helpers import session_scope, load_user
from gridt.exc import UserNotFoundError
from gridt.models import User
from gridt.util.email_templates import (
    send_password_reset_email,
    send_password_change_notification,
    send_email_change_email,
    send_email_change_notification,
)
import logging


def user_exists(user_id: int) -> bool:
    """Ensure the users exists."""
    with session_scope() as session:
        try:
            load_user(user_id, session)
        except UserNotFoundError:
            return False
        return True


def update_user_bio(user_id: int, bio: str) -> None:
    """Set the bio of user to provided bio."""
    with session_scope() as session:
        user = load_user(user_id, session)
        user.bio = bio
        session.add(user)
        session.commit()


def change_password(user_id: int, new_password: str):
    with session_scope() as session:
        user = session.query(User).get(user_id)
        user.hash_and_store_password(new_password)
        send_password_change_notification(user.email)


def change_email(user_id: int, token_string: str, secret_key):
    """Change the email of the user to the email provided in the token."""
    with session_scope() as session:
        token_decoded = jwt.decode(
            token_string, secret_key, algorithms=["HS256"]
        )
        user_id = token_decoded["user_id"]
        new_email = token_decoded["new_email"]

        user = load_user(user_id, session)
        user.email = new_email

        send_email_change_notification(user.email, user.username)


def request_email_change(user_id: int, new_email: str, secret_key: str):
    with session_scope() as session:
        user = load_user(user_id, session)

        # We cannot give a malicious user information about the e-mails in
        # our database.
        if session.query(User).filter_by(email=new_email).one_or_none():
            logging.critical(
                "Email change to known email requested by user with id: %d",
                user_id,
            )
            return

        token = user.get_email_change_token(new_email, secret_key)
        send_email_change_email(new_email, user.username, token)


def request_password_reset(email: int, secret_key: str):
    """
    Make a dictionary containing the e-mail for password reset
    + an expiration timestamp such that the token is valid for 2 hours
    and encodes it into a JWT.
    """
    with session_scope() as session:
        user = session.query(User).filter_by(email=email).one_or_none()
        if not user:
            logging.critical(
                "Attempt at resetting unregistered email: %s", email
            )
            return

        token = user.get_password_reset_token(secret_key)
        send_password_reset_email(user.email, token)


def reset_password(token: str, password: str, secret_key: str):
    with session_scope() as session:
        payload = jwt.decode(token, secret_key, algorithms=["HS256"])
        user = session.query(User).get(payload["user_id"])
        user.hash_and_store_password(password)
        send_password_change_notification(user.email)


def verify_password_for_id(user_id: int, password: str) -> int:
    with session_scope() as session:
        user = load_user(user_id, session)
        return user.verify_password(password)


def verify_password_for_email(email: str, password: str) -> int:
    with session_scope() as session:
        user = session.query(User).filter_by(email=email).one()
        if user.verify_password(password):
            return user.id
        else:
            raise ValueError("Wrong password")


def register(username: str, email: str, password: str, is_admin=False):
    with session_scope() as session:
        user = User(username, email, password, is_admin)
        session.add(user)


def get_identity(user_id: int):
    with session_scope() as session:
        user = session.get(User, user_id)
        return user.to_json(include_email=True)
