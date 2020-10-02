import jwt
from freezegun import freeze_time
from gridt.basetest import BaseTest
from gridt.models import User


class UnitTestUser(BaseTest):
    def test_create(self):
        user1 = User("username", "test@test.com", "password")

        self.assertEqual(user1.username, "username")
        self.assertEqual(user1.verify_password("password"), True)
        self.assertEqual(user1.role, "user")

        user2 = User(
            "username2", "test@test.com", "password2", role="administrator"
        )

        self.assertEqual(user2.username, "username2")
        self.assertEqual(user2.verify_password("password2"), True)
        self.assertEqual(user2.role, "administrator")

    def test_hash(self):
        user = User("username", "test@test.com", "test")
        self.assertTrue(user.verify_password("test"))

    def test_avatar(self):
        user = User("username", "test@test.com", "test")
        self.assertEqual(
            user.get_email_hash(), "b642b4217b34b1e8d3bd915fc65c4452"
        )

    def test_get_password_reset_token(self):
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
