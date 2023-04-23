"""Tests for Creation Model."""
from gridt.tests.basetest import BaseTest
from gridt.models import Creation, User, Movement
from freezegun import freeze_time
from datetime import datetime


class UnitTestCreation(BaseTest):
    """Creation Model unittests."""

    def test_init(self):
        """Unittest for __init__."""
        creation1 = None
        earlier = datetime(2022, 12, 27, 3, 36, 00)
        with freeze_time(earlier):
            creation1 = Creation()

        self.assertIsNone(creation1.movement)
        self.assertIsNone(creation1.user)
        self.assertEqual(creation1.time_added, earlier)
        self.assertEqual(creation1.type, 'creation')

        user = self.create_user()
        movement = self.create_movement()

        creation2 = None
        later = datetime(2022, 12, 27, 3, 36, 00)
        with freeze_time(later):
            creation2 = Creation(user, movement)

        self.assertEqual(creation2.movement, movement)
        self.assertEqual(creation2.user, user)
        self.assertEqual(creation2.time_added, later)
        self.assertEqual(creation2.type, 'creation')

    def test_end(self):
        """Unittest for end."""
        user = self.create_user()
        movement = self.create_movement()
        creation = Creation(user, movement)

        now = datetime(2022, 12, 27, 3, 36, 00)
        with freeze_time(now):
            creation.end()

        self.assertEqual(creation.time_removed, now)
        self.assertTrue(creation.has_ended())

    def test_repr(self):
        """Unittest for __str__."""
        user = User("abc123", "test@test.com", "password")
        movement = Movement("xyz890", "weekly", "some movement")
        creation = Creation(user, movement)
        expected = "<Creation relation: abc123 has created xyz890>"
        self.assertEqual(str(creation), expected)
