from unittest import skip
import jwt
from freezegun import freeze_time
from gridt.tests.basetest import BaseTest
from gridt.models import User, MovementUserAssociation, Movement


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

    @skip
    def test_get_change_email_token(self):
        pass

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

    def test_current_movements(self):
        """
        Movement1:
            1X 2 3
        Movement2:
            1  2 3
        Movement3:
            -
        """

        for i in range(3):
            user = self.create_user()
            movement = self.create_movement()
            self.session.add_all([user, movement])

        self.session.commit()
        movement1 = self.session.query(Movement).get(1)
        movement2 = self.session.query(Movement).get(2)
        for i in range(1, 4):
            assoc1 = MovementUserAssociation(
                movement1, self.session.query(User).get(i)
            )
            assoc2 = MovementUserAssociation(
                movement2, self.session.query(User).get(i)
            )
            self.session.add_all([assoc1, assoc2])

        self.session.commit()
        self.session.query(MovementUserAssociation).get(1).destroy()
        self.session.commit()

        user1 = self.session.query(User).get(1)
        user2 = self.session.query(User).get(2)

        self.assertEqual(user1.current_movements, [movement2])
        self.assertEqual(
            user2.current_movements,
            [movement1, movement2],
        )
