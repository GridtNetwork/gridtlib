"""Tests for User Model."""
from unittest import skip
import jwt
from freezegun import freeze_time
from gridt.tests.basetest import BaseTest
from gridt.models import User


class UnitTestUser(BaseTest):
    """User Model unittests."""

    def test_create(self):
        """Unittest for __init__."""
        user1 = User("username", "test@test.com", "password")

        self.assertEqual(user1.username, "username")
        self.assertEqual(user1.verify_password("password"), True)
        self.assertEqual(user1.is_admin, False)

        user2 = User(
            "username2", "test@test.com", "password2", is_admin=True
        )

        self.assertEqual(user2.username, "username2")
        self.assertEqual(user2.verify_password("password2"), True)
        self.assertEqual(user2.is_admin, True)

    def test_hash(self):
        """Unittest for hash_and_store_password."""
        user = User("username", "test@test.com", "test")
        self.assertTrue(user.verify_password("test"))

    def test_avatar(self):
        """Unittest for get avatar."""
        user = User("username", "test@test.com", "test")
        self.assertEqual(
            user.get_email_hash(), "b642b4217b34b1e8d3bd915fc65c4452"
        )

    @skip
    def test_get_change_email_token(self):
        """Unittest for get_change_email_token."""
        pass

    def test_get_password_reset_token(self):
        """Unittest for get_password_reset_token."""
        user = self.create_user()
        self.session.commit()

        with freeze_time("2020-04-18 22:10:00"):
            self.assertEqual(
                jwt.decode(
                    user.get_password_reset_token("secret"),
                    "secret",
                    algorithms=["HS256"],
                ),
                {"user_id": user.id, "exp": 1587255000.0},
            )
