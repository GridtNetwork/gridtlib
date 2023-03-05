from gridt.tests.basetest import BaseTest

from gridt.controllers.announcement import (
    create_announcement,
    update_announcement,
    delete_announcement,
    get_announcements,
    add_json_announcement_details,
    _get_announcement
)
from gridt.controllers.user import (
    register,
    verify_password_for_email,
    get_identity
)
from gridt.controllers.creation import new_movement_by_user
from gridt.controllers.movements import get_movement
from gridt.controllers.helpers import GridtExceptions as E

from gridt.models import Announcement

from freezegun import freeze_time

from datetime import datetime

class UnitTestsAnnouncementController(BaseTest):

    def test_create_announcement(self):
        movement = self.create_movement()
        user = self.create_user()
        self.session.commit()

        movement_id = movement.id
        user_id = user.id
        message = "Hello, this is a new announcement"
        expected = {
            "id": 1,
            "movement_id": movement_id,
            "poster": user.to_json(),
            "message": message,
            "created_time": datetime(2023, 2, 25, 16, 30, 0),
            "updated_time": None
        }

        # Check errors
        with self.assertRaises(E.MovementNotFoundError):
            create_announcement(movement_id=movement_id+1, message=message, user_id=user_id)
        with self.assertRaises(E.UserNotFoundError):
            create_announcement(movement_id=movement_id, message=message, user_id=user_id+1)

        with freeze_time("2023-02-25 16:30:00"):
            announcement_json = create_announcement(movement_id=movement_id, message=message, user_id=user_id)

        self.assertDictEqual(announcement_json, expected)

    def test_update_announcement(self):
        movement = self.create_movement()
        user = self.create_user()

        with freeze_time("2023-02-25 17:00:00"):
            announcement = Announcement(movement, "Hello, this is new annoucement", user)
        
        self.session.add(announcement)
        self.session.commit()

        announcement_id = announcement.id
        user_id = user.id

        # Check errors
        with self.assertRaises(E.UserNotFoundError):
            update_announcement("", announcement_id, user_id+1)
        with self.assertRaises(E.AnnouncementNotFoundError):
            update_announcement("", announcement_id+1, user_id)

        with freeze_time("2023-02-25 16:30"):
            update_announcement("Hello, this is a new announcement", announcement_id, user_id)

        updated_announcement = self.session.query(Announcement).filter(
            Announcement.id == announcement_id
        ).one()

        self.assertEqual("Hello, this is a new announcement", updated_announcement.message)
        
    def test_delete_announcement(self):
        movement = self.create_movement()
        user = self.create_user()
        announcement = Announcement(movement, "Hello, this is a new announcement", user)
        self.session.add(announcement)
        self.session.commit()

        announcement_id = announcement.id
        user_id = user.id

        # Check errors
        with self.assertRaises(E.UserNotFoundError):
            delete_announcement(announcement_id, user_id+1)
        with self.assertRaises(E.AnnouncementNotFoundError):
            delete_announcement(announcement_id+1, user_id)

        with freeze_time("2023-02-25 21:00:00"):
            delete_announcement(announcement_id, user_id)

        self.assertEqual(1, self.session.query(Announcement).filter(
            Announcement.removed_time == datetime(2023, 2, 25, 21, 0, 0)
        ).count())

    def test_get_announcement(self):
        movement = self.create_movement()
        user = self.create_user()
        with freeze_time("2023-02-25 18:30:00"):
            announcement = Announcement(movement, "Welcome to the movement!", user)
        self.session.add(announcement)
        self.session.commit()

        announcement_id = announcement.id

        # Check the error
        with self.assertRaises(E.AnnouncementNotFoundError):
            _get_announcement(announcement_id + 1, self.session)

        self.assertEqual(
            self.session.query(Announcement).get(announcement_id),
            _get_announcement(announcement_id, self.session)
        )

    def test_get_announcements(self):
        movement = self.create_movement()
        user = self.create_user()
        with freeze_time("2023-02-25 18:30:00"):
            announcement1 = Announcement(movement, "Welcome to the movement!", user)
        with freeze_time("2023-02-25 18:32:00"):
            announcement2 = Announcement(movement, "Lets make the world a better place! or something?", user)
        self.session.add_all([announcement1, announcement2])
        self.session.commit()

        json_1 = announcement1.to_json()
        json_2 = announcement2.to_json()
        movement_id = movement.id

        self.assertListEqual([json_2, json_1], get_announcements(movement_id))

    def test_add_json_announcement_details(self):
        movement = self.create_movement()
        user = self.create_user()
        with freeze_time("2023-02-25 19:00:00"):
            announcement = Announcement(movement, "Hello, this is a new announcement", user)
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

    def test_make_movement_announcements(self):
        """
        As an administrator I would like to be able to make a announcements for movements.
        """
        register('Antonin', 'antonin.thioux@gmail.com', 'password123')
        antonin_id = verify_password_for_email('antonin.thioux@gmail.com', 'password123')

        with freeze_time("2023-02-25 12:00:00"):
            movement_1_json = new_movement_by_user(antonin_id, "Meditate everyday", 'daily')['movement']
            movement_2_json = new_movement_by_user(antonin_id, "Run once a week", 'weekly')['movement']
        
        m1_id, m2_id = movement_1_json['id'], movement_2_json['id']

        with freeze_time("2023-02-26 11:00:00"):
            a1_json = create_announcement("Welcome to the meditate everyday movement! Namaste.", m1_id, antonin_id)

        self.assertDictEqual(a1_json, get_movement(m1_id, antonin_id)['last_announcement'])
        self.assertIsNone(get_movement(m2_id, antonin_id)['last_announcement'])

        with freeze_time("2023-02-26 12:00:00"):
            a2_json = create_announcement("Welcome to run once a week movement!", m2_id, antonin_id)
            a3_json = create_announcement(
                "New research shows that only 17 minutes of mediation a day gives benefits",
                 m1_id,
                 antonin_id
            )

        self.assertDictEqual(a3_json, get_movement(m1_id, antonin_id)['last_announcement'])
        self.assertDictEqual(a2_json, get_movement(m2_id, antonin_id)['last_announcement'])
        self.assertEqual(3, self.session.query(Announcement).filter(Announcement.poster_id == antonin_id).count())

    def test_update_movement_announcements(self):
        """
        As an administrator I would like to be able to update announcements
        """
        register('Antonin', 'antonin.thioux@gmail.com', 'password123')
        antonin_id = verify_password_for_email('antonin.thioux@gmail.com', 'password123')
        antonin_json = get_identity(antonin_id)
        del antonin_json['email']  # Email should be private

        with freeze_time("2023-02-25 12:00:00"):
            movement_json = new_movement_by_user(antonin_id, "Floss daily", 'daily')['movement']

        m_id = movement_json['id']

        with freeze_time("2023-02-25 13:00:00"):
            welcome_message = "Welcome to the new movement!"
            welcome_announcement_json = create_announcement(welcome_message, m_id, antonin_id)
            welcome_id = welcome_announcement_json['id']
        with freeze_time("2023-02-25 13:30:00"):
            info_message = "Find out more information on flossing"
            info_announcement_json = create_announcement(info_message, m_id, antonin_id)
            info_id = info_announcement_json['id']
        with freeze_time("2023-02-25 15:00:00"):
            welcome_message += "\nFollow us on FaceBook!"
            update_announcement(welcome_message, welcome_id, antonin_id)

        expected_welcome_json = {
            'id': welcome_id,
            'movement_id': m_id,
            'message': welcome_message,
            'poster': antonin_json,
            'created_time': datetime(2023, 2, 25, 13, 0),
            'updated_time': datetime(2023, 2, 25, 15, 0)
        }
        self.assertEqual(
            expected_welcome_json,
            self.session.query(Announcement).filter(Announcement.id == welcome_id).one().to_json()
        )
        self.assertEqual(
            info_announcement_json,
            self.session.query(Announcement).filter(Announcement.id == info_id).one().to_json()
        )

        with freeze_time("2023-02-26 14:00:00"):
            habit_message = "motivation is what gets you started. habit is what keeps you going"
            habit_announcement_json = create_announcement(habit_message, m_id, antonin_id)
            habit_id = habit_announcement_json['id']
        with freeze_time("2023-02-26 14:05:00"):
            habit_message = "Motivation is what gets you started, habit is what keeps you going"
            update_announcement(habit_message, habit_id, antonin_id)
            update_announcement(habit_message + "!", habit_id, antonin_id)
            info_message += " on our facebook page!"
            update_announcement(info_message, info_id, antonin_id)

        expected_info_json = {
            'id': info_id,
            'movement_id': m_id,
            'message': info_message,
            'poster': antonin_json,
            'created_time': datetime(2023, 2, 25, 13, 30),
            'updated_time': datetime(2023, 2, 26, 14, 5)
        }
        expected_habit_json = {
            'id': habit_id,
            'movement_id': m_id,
            'message': habit_message + "!",
            'poster': antonin_json,
            'created_time': datetime(2023, 2, 26, 14, 0),
            'updated_time': datetime(2023, 2, 26, 14, 5)
        }
        self.assertDictEqual(
            expected_welcome_json,
            self.session.query(Announcement).filter(Announcement.id == welcome_id).one().to_json()
        )
        self.assertDictEqual(
            expected_info_json,
            self.session.query(Announcement).filter(Announcement.id == info_id).one().to_json()
        )
        self.assertDictEqual(
            expected_habit_json,
            self.session.query(Announcement).filter(Announcement.id == habit_id).one().to_json()
        )

    def test_delete_movement_announcements(self):
        """
        As an administrator I would like to be able to delete announcements
        """
        register('Antonin', 'antonin.thioux@gmail.com', 'password123')
        antonin_id = verify_password_for_email('antonin.thioux@gmail.com', 'password123')

        with freeze_time("2023-02-25 12:00:00"):
            movement_1_json = new_movement_by_user(antonin_id, "Floss daily", 'daily')['movement']
            movement_2_json = new_movement_by_user(antonin_id, "Run once a week", 'weekly')['movement']

        m1_id, m2_id = movement_1_json['id'], movement_2_json['id']

        with freeze_time("2023-02-25 13:00:00"):
            welcome_message = "Welcome to the new movement!"
            welcome1_announcement_json = create_announcement(welcome_message, m1_id, antonin_id)
            welcome2_announcement_json = create_announcement(welcome_message, m2_id, antonin_id)
            welcome1_id = welcome1_announcement_json['id']

        with freeze_time("2023-02-25 14:00:00"):
            wrong_chat_message = "We can use chatGPT to write the assignment UwU"
            wrong_announcement_json = create_announcement(wrong_chat_message, m1_id, antonin_id)
            wrong_id = wrong_announcement_json['id']

        with freeze_time("2023-02-26 14:30:00"):
            delete_announcement(welcome1_id, antonin_id)
            delete_announcement(wrong_id, antonin_id)

        self.assertIsNone(get_movement(m1_id, antonin_id)['last_announcement'])
        self.assertListEqual([], get_announcements(m1_id))
        self.assertDictEqual(welcome2_announcement_json, get_movement(m2_id, antonin_id)['last_announcement'])
        self.assertListEqual([welcome2_announcement_json], get_announcements(m2_id))
    
    def test_view_announcements(self):
        """
        As a subscriber to a movement I would like to be able to view the movement's announcements
        """
        register('Antonin', 'antonin.thioux@gmail.com', 'password123')
        antonin_id = verify_password_for_email('antonin.thioux@gmail.com', 'password123')

        with freeze_time("2023-02-25 12:00:00"):
            movement_1_json = new_movement_by_user(antonin_id, "Meditate everyday", 'daily')['movement']
            movement_2_json = new_movement_by_user(antonin_id, "Run once a week", 'weekly')['movement']
        
        m1_id, m2_id = movement_1_json['id'], movement_2_json['id']

        with freeze_time("2023-02-26 11:00:00"):
            a1_json = create_announcement("Welcome to the meditate everyday movement! Namaste.", m1_id, antonin_id)
        with freeze_time("2023-02-26 14:00:00"):
            a2_json = create_announcement("Find out which meditation practice works best for you", m1_id, antonin_id)
        with freeze_time("2023-02-26 15:00:00"):
            a3_json = create_announcement("Watch our HD meditation videos on YouTube!", m1_id, antonin_id)
        with freeze_time("2023-02-26 16:00:00"):
            a4_json = create_announcement("Happiness comes from within, Buy our new merch!", m1_id, antonin_id)

        self.assertListEqual([a4_json, a3_json, a2_json, a1_json], get_announcements(m1_id))
        self.assertDictEqual(a4_json, get_movement(m1_id, antonin_id)['last_announcement'])
        self.assertListEqual([], get_announcements(m2_id))
        self.assertIsNone(get_movement(m2_id, antonin_id)['last_announcement'])
