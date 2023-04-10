"""Test for movement controller."""
from freezegun import freeze_time
from unittest import skip

from gridt.tests.basetest import BaseTest
from gridt.models import Movement, Subscription, UserToUserLink

from gridt.controllers.leader import send_signal
from gridt.controllers.movements import (
    get_movement,
    create_movement,
    movement_name_exists
)

from datetime import datetime


class MovementControllerUnitTests(BaseTest):
    """Unittest for movement controller."""

    def test_create_movement(self):
        """Unittest for create_movement."""
        create_movement(
            name="movement1",
            interval="daily",
            short_description="Hi",
            description="A long description",
            session=self.session
        )

        movement = self.session.get(Movement, 1)
        self.assertTrue(movement is not None)

        expected = {
            "id": 1,
            "name": "movement1",
            "short_description": "Hi",
            "description": "A long description",
            "interval": "daily",
        }

        self.assertDictEqual(expected, movement.to_json())

    def test_get_movement(self):
        """Unittest for get_movement."""
        movement = Movement(
            "movement1",
            "daily",
            short_description="Hi",
            description="A long description",
        )
        user_1 = self.create_user()
        user_2 = self.create_user(generate_bio=True)
        subscription_1 = Subscription(user_1, movement)
        subscription_2 = Subscription(user_2, movement)
        user_to_user_link1 = UserToUserLink(movement, user_1, user_2)
        user_to_user_link2 = UserToUserLink(movement, user_2, user_1)

        self.session.add_all([
            movement,
            subscription_1, subscription_2,
            user_to_user_link1, user_to_user_link2
        ])
        self.session.commit()

        u1_id, u2_id, m_id = user_1.id, user_2.id, movement.id

        now = datetime(1995, 1, 15, 12)
        later = datetime(1996, 3, 15, 8)

        message = "This is a message"

        with freeze_time(now):
            send_signal(u1_id, m_id)
        with freeze_time(later):
            send_signal(u2_id, m_id, message=message)

        with freeze_time(now):
            send_signal(u1_id, m_id)
        with freeze_time(later):
            send_signal(u2_id, m_id, message=message)

        self.session.add_all([user_1, user_2, movement])

        user_dict = user_1.to_json()
        user_dict["last_signal"] = {"time_stamp": str(now.astimezone())}
        expected = {
            "id": 1,
            "name": "movement1",
            "short_description": "Hi",
            "description": "A long description",
            "interval": "daily",
            "last_announcement": None,
            "subscribed": True,
            "leaders": [user_dict],
            "last_signal_sent": {
                "time_stamp": str(later.astimezone()),
                "message": "This is a message"
            },
        }
        self.assertDictEqual(get_movement(movement.id, user_2.id), expected)

    def test_movement_name_exists(self):
        """Unittest for movement_name_exists."""
        movement = self.create_movement()
        name = movement.name
        not_name = "Not " + name
        self.session.commit()

        self.assertTrue(movement_name_exists(movement_name=name))
        self.assertFalse(movement_name_exists(movement_name=not_name))


class MovementControllerIntergrationTests(BaseTest):
    """User stories tests for movement controller."""

    @skip
    def test_create_and_get_movement(self):
        """As a user I would like to see a list of movements."""
        pass
