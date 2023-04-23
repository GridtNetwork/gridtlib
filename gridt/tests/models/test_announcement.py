"""Tests for Announement Model."""
from gridt.tests.basetest import BaseTest
from gridt.models import Announcement

from freezegun import freeze_time
from datetime import datetime


class UnitTestAnnouncementModel(BaseTest):
    """Announcement Model unittests."""

    def test_init(self):
        """Unittest for __init__."""
        movement = self.create_movement()
        user = self.create_user()
        message = "This is a dummy announcement, Hello World!"

        now = datetime(2023, 2, 20, 14, 0)
        with freeze_time(now):
            announcement = Announcement(movement, message, user)

        self.session.add(announcement)
        self.session.commit()

        self.assertEqual(announcement.message, message)
        self.assertEqual(announcement.created_time, now)
        self.assertEqual(announcement.movement, movement)

    def test_str(self):
        """Unittest for __str__."""
        movement = self.create_movement()
        user = self.create_user()
        message = "This is a dummy announcement, Hello World!"
        announcement = Announcement(movement, message, user)
        self.session.add(announcement)
        self.session.commit()
        expected = f"Announcement for movement 1: {message}"
        self.assertEqual(str(announcement), expected)

    def test_to_json(self):
        """Unittest for to_json."""
        movement = self.create_movement()
        user = self.create_user()
        message = "This is a dummy announcement, Hello World!"

        now = datetime(2023, 2, 25, 16, 0)
        with freeze_time(now):
            announcement = Announcement(movement, message, user)

        self.session.add(announcement)
        self.session.commit()

        announcement_id = announcement.id
        movement_id = movement.id

        self.assertDictEqual(announcement.to_json(), {
            "id": announcement_id,
            "movement_id": movement_id,
            "poster": user.to_json(),
            "message": message,
            "created_time": str(now.astimezone()),
            "updated_time": None
        })

    def test_update_message(self):
        """Unittest for update_message."""
        movement = self.create_movement()
        user = self.create_user()
        message = "This is a dummy announcement, Hello World!"
        announcement = Announcement(movement, message, user)

        now = datetime(2023, 2, 25, 20, 0, 0)
        with freeze_time(now):
            message = "This is an announcement, Hello!"
            announcement.update_message(message)

        self.assertEqual(message, announcement.message)
        self.assertEqual(now, announcement.updated_time)

    def test_remove(self):
        """Unittest for remove."""
        movement = self.create_movement()
        user = self.create_user()
        message = "This is a dummy announcement, Hello World!"
        announcement = Announcement(movement, message, user)

        now = datetime(2023, 2, 25, 20, 0, 0)
        with freeze_time(now):
            announcement.remove()

        self.assertEqual(now, announcement.removed_time)
