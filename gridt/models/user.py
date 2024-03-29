"""Model for user in the database."""
import datetime
import jwt
from sqlalchemy import Column, Integer, String, UnicodeText, Boolean

from passlib.apps import custom_app_context as pwd_context
import hashlib

from gridt.db import Base


class User(Base):
    """
    Intuitive representation of users in the database.

    :param str username: Username that the user has chosen.
    :param str email: Email that the user has chosen.
    :param str password: Password that the user has chosen.
    :param str bio: Small biography of the uesr.

    :attribute password_hash: Hashed version of the users's password.
    :attribute follower_associations: All associations to movements where the
        follower is this user. Useful for determining the leaders of a user.
    :attribute movements: List of all movements that the user is subscribed to.
    """

    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(32))
    email = Column(String(40), unique=True, nullable=False)
    password_hash = Column(String(128))
    is_admin = Column(Boolean())
    bio = Column(UnicodeText)

    def __init__(self, username, email, password, is_admin=False, bio=""):
        """Construct a new user."""
        self.username = username
        self.email = email
        self.hash_and_store_password(password)
        self.is_admin = is_admin
        self.bio = bio

    def __repr__(self):
        """Get the string representation of the user."""
        return f"<User username={self.username}>"

    def hash_and_store_password(self, password):
        """
        Hash password and set it as the password_hash.

        :param str password: Password that is to be hashed.
        """
        self.password_hash = pwd_context.hash(password)

    def get_email_hash(self):
        """Hash e-mail with md5."""
        h = hashlib.md5()
        h.update(bytes(self.email, "utf-8"))
        email_hash = h.hexdigest()
        return email_hash

    def verify_password(self, password):
        """
        Verify that this password matches with the saved password hash.

        :rtype bool:
        """
        return pwd_context.verify(password, self.password_hash)

    def get_password_reset_token(self, secret_key):
        """Get a token to reset the user's password."""
        now = datetime.datetime.now()
        valid = datetime.timedelta(hours=2)
        exp = now + valid
        exp = exp.timestamp()

        payload = {"user_id": self.id, "exp": exp}

        token = jwt.encode(payload, secret_key, algorithm="HS256")
        return token

    def get_email_change_token(self, new_email, secret_key):
        """
        Get a token to change the user's email.

        Make a dictionary containing the user's id, new email
        + an expiration timestamp such that the token is valid for 2 hours
        and encodes it into a JWT.
        :param str new_email: The new e-mail that needs to be verified.
        :rtype str: the JWT that is used to verify the e-mail change.
        """
        now = datetime.datetime.now()
        valid = datetime.timedelta(hours=2)
        exp = now + valid
        exp = exp.timestamp()

        secret_key = secret_key

        token_dict = {"user_id": self.id, "new_email": new_email, "exp": exp}

        token = jwt.encode(token_dict, secret_key, algorithm="HS256")
        return token

    def to_json(self, include_email=False):
        """Compute the json representation of the json."""
        res = {
            "id": self.id,
            "username": self.username,
            "bio": self.bio,
            "avatar": self.get_email_hash(),
            "is_admin": self.is_admin,
        }
        if include_email:
            res["email"] = self.email
        return res
