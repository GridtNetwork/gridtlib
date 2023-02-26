from gridt.tests.basetest import BaseTest
from gridt.models import Announcement

from freezegun import freeze_time
from datetime import datetime

class UnitTestAnnouncmentModel(BaseTest):
    
    def test_init(self):
        movement = self.create_movement()
        user = self.create_user()
        message = "This is a dummy announcement, Hello World!"

        with freeze_time("2023-02-20 14:00:00"):
            announcement = Announcement(movement, message, user)

        self.session.add(announcement)
        self.session.commit()

        self.assertEqual(announcement.message, message)
        self.assertEqual(announcement.created_time, datetime(2023, 2, 20, 14, 0))
        self.assertEqual(announcement.movement, movement)

    def test_str(self):
        movement = self.create_movement()
        user = self.create_user()
        message = "This is a dummy announcement, Hello World!"
        announcement = Announcement(movement, message, user)
        self.session.add(announcement)
        self.session.commit()
        self.assertEqual(str(announcement), f"Announcement for movement 1: {message}")
    
    def test_to_json(self):
        movement = self.create_movement()
        user = self.create_user()
        message = "This is a dummy announcement, Hello World!"

        with freeze_time("2023-02-25 16:00:00"):
            announcement = Announcement(movement, message, user)
        
        self.session.add(announcement)
        self.session.commit()

        announcement_id = announcement.id
        movement_id = movement.id

        self.assertDictEqual(announcement.to_json(), {
            "id": announcement_id,
            "movement_id": movement_id,
            "message": message,
            "created_time": datetime(2023, 2, 25, 16, 0),
            "updated_time": None
        })

    def test_update_message(self):
        movement = self.create_movement()
        user = self.create_user()
        message = "This is a dummy announcement, Hello World!"
        announcement = Announcement(movement, message, user)

        with freeze_time("2023-02-25 20:00:00"):
            announcement.update_message("This is an announcement, Hello!")
        
        self.assertEqual("This is an announcement, Hello!", announcement.message)
        self.assertEqual(datetime(2023, 2, 25, 20, 0, 0), announcement.updated_time)

    def test_remove(self):
        movement = self.create_movement()
        user = self.create_user()
        message = "This is a dummy announcement, Hello World!"
        announcement = Announcement(movement, message, user)

        with freeze_time("2023-02-25 20:00:00"):
            announcement.remove()

        self.assertEqual(datetime(2023, 2, 25, 20, 0, 0), announcement.removed_time)
