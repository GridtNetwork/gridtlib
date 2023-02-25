from gridt.tests.basetest import BaseTest

from gridt.controllers.announcement import (
    create_announcement,
    update_announcement,
    delete_announcement,
    get_announcements,
    add_json_announcement_details
)

from gridt.models import Announcement

from unittest import skip
from freezegun import freeze_time

from datetime import datetime

class UnitTestsAnnouncementController(BaseTest):

    def test_create_announcement(self):
        movement = self.create_movement()
        self.session.commit()

        movement_id = movement.id
        message = "Hello, this is a new announcement"
        expected = {
            "id": 1,
            "movement_id": movement_id,
            "message": message,
            "created_time": datetime(2023, 2, 25, 16, 30, 0),
            "updated_time": None
        }

        with freeze_time("2023-02-25 16:30:00"):
            announcement_json = create_announcement(movement_id=movement_id, message=message)

        self.assertDictEqual(announcement_json, expected)

    def test_update_announcement(self):
        movement = self.create_movement()

        with freeze_time("2023-02-25 17:00:00"):
            announcement = Announcement(movement, "Hello, this is new annoucement")
        
        self.session.add(announcement)
        self.session.commit()

        announcement_id = announcement.id
        expected = announcement.to_json()

        with freeze_time("2023-02-25 16:30"):
            announcement_json = update_announcement("Hello, this is a new announcement", announcement_id)

        self.assertDictEqual(announcement_json, expected)

        updated_announcement = self.session.query(Announcement).filter(
            Announcement.id == announcement_id
        ).one()

        self.assertEqual("Hello, this is a new announcement", updated_announcement.message)
        
    def test_delete_announcement(self):
        movement = self.create_movement()
        announcement = Announcement(movement, "Hello, this is a new announcement")
        self.session.add(announcement)
        self.session.commit()

        expected_json = announcement.to_json()

        with freeze_time("2023-02-25 21:00:00"):
            announcement_json = delete_announcement(announcement.id)

        self.assertDictEqual(announcement_json, expected_json)
        self.assertEqual(1, self.session.query(Announcement).filter(
            Announcement.removed_time == datetime(2023, 2, 25, 21, 0, 0)
        ).count())

    def test_get_announcements(self):
        movement = self.create_movement()
        with freeze_time("2023-02-25 18:30:00"):
            announcement1 = Announcement(movement, "Welcome to the movement!")
        with freeze_time("2023-02-25 18:32:00"):
            announcement2 = Announcement(movement, "Lets make the world a better place! or something?")
        self.session.add_all([announcement1, announcement2])
        self.session.commit()

        json_1 = announcement1.to_json()
        json_2 = announcement2.to_json()
        movement_id = movement.id

        self.assertListEqual([json_2, json_1], get_announcements(movement_id))

    def test_add_json_announcement_details(self):
        movement = self.create_movement()
        with freeze_time("2023-02-25 19:00:00"):
            announcement = Announcement(movement, "Hello, this is a new announcement")
        self.session.add(announcement)
        self.session.commit()

        announcement_json = announcement.to_json()
        json = {'foo': 1, 'bar': ['arr']}
        base_json = json.copy()
        add_json_announcement_details(json, movement, self.session)
        
        self.assertEqual(json, {**json, **base_json}) # json == json | base_json
        self.assertDictEqual(json['last_announcement'], announcement_json)


class TestUserStoriesAnnouncementController(BaseTest):
    """
    TODO: Some of the User Stories should be for admins only.
    These user stories should be updated once roles are implemented.
    """

    @skip
    def test_make_movement_announcements(self):
        """
        As an administrator I would like to be able to make a announcements for movements.
        """
        pass

    @skip
    def test_update_movement_announcements(self):
        """
        As an administrator I would like to be able to update announcements
        """
        pass

    @skip
    def test_delete_movement_announcements(self):
        """
        As an administrator I would like to be able to delete announcements
        """
        pass
    
    @skip
    def test_view_announcements(self):
        """
        As a subscriber to a movement I would like to be able to view announcements in the movements I am subscribed too
        """
        pass
