import datetime
import jwt
from sqlalchemy import Column, Integer, String, UnicodeText
from sqlalchemy.orm import relationship, object_session
from sqlalchemy.ext.associationproxy import association_proxy

from passlib.apps import custom_app_context as pwd_context
import hashlib

from gridt.db import Base
from .movement_user_association import MovementUserAssociation


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

    :todo: Make a user.leaders dictionary attribute that has movements as the
        keys and lists of leaders as the values. Right now this is solved with
        the leaders method.
    """

    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(32))
    email = Column(String(40), unique=True, nullable=False)
    password_hash = Column(String(128))
    role = Column(String(32))
    bio = Column(UnicodeText)

    follower_associations = relationship(
        "MovementUserAssociation",
        foreign_keys="MovementUserAssociation.follower_id"
    )

    movements = association_proxy(
        "follower_associations",
        "movement",
        creator=lambda movement: MovementUserAssociation(movement=movement),
    )

    @property
    def current_movements(self):
        # To prevent circular imports this is done here
        from .movement import Movement

        return (
            object_session(self).query(Movement)
            .join(MovementUserAssociation)
            .filter(
                MovementUserAssociation.movement_id == Movement.id,
                MovementUserAssociation.follower_id == self.id,
                MovementUserAssociation.destroyed is None,
            )
            .group_by(Movement.id)
            .all()
        )

    def __init__(self, username, email, password, role="user", bio=""):
        self.username = username
        self.email = email
        self.hash_and_store_password(password)
        self.role = role
        self.bio = bio

    def __repr__(self):
        return f"<User username={self.username}>"

    def hash_and_store_password(self, password):
        """
        Hash password and set it as the password_hash.
        :param str password: Password that is to be hashed.
        """
        self.password_hash = pwd_context.hash(password)

    def get_email_hash(self):
        """
        Hash e-mail with md5.
        """
        h = hashlib.md5()
        h.update(bytes(self.email, "utf-8"))
        email_hash = h.hexdigest()
        return email_hash

    def verify_password(self, password):
        """
        Verify that this password matches with the hashed version in the
        database.

        :rtype bool:
        """
        return pwd_context.verify(password, self.password_hash)

    def get_password_reset_token(self, secret_key):
        now = datetime.datetime.now()
        valid = datetime.timedelta(hours=2)
        exp = now + valid
        exp = exp.timestamp()

        payload = {"user_id": self.id, "exp": exp}

        token = jwt.encode(payload, secret_key, algorithm="HS256").decode(
            "utf-8"
        )
        return token

    def dictify(self, include_email=False):
        res = {
            "id": self.id,
            "username": self.username,
            "bio": self.bio,
            "avatar": self.get_email_hash(),
        }
        if include_email:
            res["email"] = self.email
        return res
