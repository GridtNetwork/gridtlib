"""Tests for Subscription Model."""
from gridt.tests.basetest import BaseTest
from gridt.models import Subscription, User, Movement
from freezegun import freeze_time
from datetime import datetime


class UnitTestSubscription(BaseTest):
    """Subscription Model unittests."""

    def test_init(self):
        """Unittest for __init__."""
        ealier = datetime(2022, 12, 27, 3, 10, 00)
        with freeze_time(ealier):
            subscription1 = Subscription()

        self.assertIsNone(subscription1.movement)
        self.assertIsNone(subscription1.user)
        self.assertEqual(subscription1.time_added, ealier)
        self.assertEqual(subscription1.type, 'subscription')

        user = self.create_user()
        movement = self.create_movement()

        later = datetime(2022, 12, 27, 1, 54, 00)
        with freeze_time(later):
            subscription2 = Subscription(user, movement)

        self.assertEqual(subscription2.movement, movement)
        self.assertEqual(subscription2.user, user)
        self.assertEqual(subscription2.time_added, later)
        self.assertEqual(subscription2.type, 'subscription')

    def test_unsubscribe(self):
        """Unittest for unsubscribe."""
        user = self.create_user()
        movement = self.create_movement()
        subscription = Subscription(user, movement)

        now = datetime(2022, 12, 27, 1, 54, 00)
        with freeze_time(now):
            subscription.unsubscribe()

        self.assertEqual(subscription.time_removed, now)
        self.assertTrue(subscription.has_ended())

    def test_repr(self):
        """Unittest for __str__."""
        user = User("abc123", "test@test.com", "password")
        movement = Movement("xyz890", "weekly", "some movement")
        subscription = Subscription(user, movement)
        expected = "<Subscription relation: abc123 is subscribed to xyz890>"
        self.assertEqual(str(subscription), expected)
