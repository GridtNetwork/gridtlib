from gridt.tests.basetest import BaseTest
from gridt.models import Announcement

from freezegun import freeze_time
from datetime import datetime

class UnitTestAnnouncmentModel(BaseTest):
    
    def test_init(self):
        movement = self.create_movement()
        message = "This is a dummy announcement, Hello World!"

        with freeze_time("2023-02-20 14:00:00"):
            announcement = Announcement(movement, message)

        self.session.add(announcement)
        self.session.commit()

        self.assertEqual(announcement.message, message)
        self.assertEqual(announcement.timestamp, datetime(2023, 2, 20, 14, 0))
        self.assertEqual(announcement.movement, movement)

    def test_str(self):
        movement = self.create_movement()
        message = "This is a dummy announcement, Hello World!"
        announcement = Announcement(movement, message)
        self.session.add(announcement)
        self.session.commit()
        self.assertEqual(str(announcement), f"Announcement for movement 1: {message}")
    
    def test_to_json(self):
        movement = self.create_movement()
        message = "This is a dummy announcement, Hello World!"

        with freeze_time("2023-02-25 16:00:00"):
            announcement = Announcement(movement, message)
        
        self.session.add(announcement)
        self.session.commit()

        announcement_id = announcement.id
        movement_id = movement.id

        self.assertDictEqual(announcement.to_json(), {
            "id": announcement_id,
            "movement_id": movement_id,
            "message": message,
            "time": datetime(2023, 2, 25, 16, 0)
        })