"""Test for announcement controller."""
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
    """Unittests for annoucnement controller."""

    def test_create_announcement(self):
        """Unittest for create_announcement."""
        movement = self.create_movement()
        user = self.create_user(is_admin=True)
        self.session.commit()

        movement_id = movement.id
        user_id = user.id
        message = "Hello, this is a new announcement"
        expected = {
            "id": 1,
            "movement_id": movement_id,
            "poster": user.to_json(),
            "message": message,
            "created_time": str(datetime(2023, 2, 25, 16, 30, 0).astimezone()),
            "updated_time": None
        }

        # Check errors
        with self.assertRaises(E.MovementNotFoundError):
            create_announcement(
                movement_id=movement_id+1, message=message, user_id=user_id
            )
        with self.assertRaises(E.UserNotFoundError):
            create_announcement(
                movement_id=movement_id, message=message, user_id=user_id+1
            )

        with freeze_time("2023-02-25 16:30:00"):
            announcement_json = create_announcement(
                movement_id=movement_id, message=message, user_id=user_id
            )

        self.assertDictEqual(announcement_json, expected)

    def test_update_announcement(self):
        """Unittest for update_announcement."""
        movement = self.create_movement()
        user = self.create_user(is_admin=True)

        with freeze_time("2023-02-25 17:00:00"):
            message = "Hello, this is new annoucement"
            announcement = Announcement(movement, message, user)

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
            new_message = "Hello, this is a new announcement"
            update_announcement(new_message, announcement_id, user_id)

        updated_announcement = self.session.query(Announcement).filter(
            Announcement.id == announcement_id
        ).one()

        self.assertEqual(new_message, updated_announcement.message)

    def test_delete_announcement(self):
        """Unittest for delete_announcement."""
        movement = self.create_movement()
        user = self.create_user(is_admin=True)
        message = "Hello, this is a new announcement"
        announcement = Announcement(movement, message, user)
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
        """Unittest for _get_announcement."""
        movement = self.create_movement()
        user = self.create_user()
        with freeze_time("2023-02-25 18:30:00"):
            message = "Welcome to the movement!"
            announcement = Announcement(movement, message, user)
        self.session.add(announcement)
        self.session.commit()

        announcement_id = announcement.id

        # Check the error
        with self.assertRaises(E.AnnouncementNotFoundError):
            _get_announcement(announcement_id + 1, self.session)

        self.assertEqual(
            self.session.get(Announcement, announcement_id),
            _get_announcement(announcement_id, self.session)
        )

    def test_get_announcements(self):
        """Unittest for get announcements."""
        movement = self.create_movement()
        user = self.create_user()
        with freeze_time("2023-02-25 18:30:00"):
            message1 = "Welcome to the movement!"
            announcement1 = Announcement(movement, message1, user)
        with freeze_time("2023-02-25 18:32:00"):
            message2 = "Lets make the world a better place! or something?"
            announcement2 = Announcement(movement, message2, user)
        self.session.add_all([announcement1, announcement2])
        self.session.commit()

        json_1 = announcement1.to_json()
        json_2 = announcement2.to_json()
        movement_id = movement.id

        self.assertListEqual([json_2, json_1], get_announcements(movement_id))

    def test_add_json_announcement_details(self):
        """Unittest for get_announcement_details."""
        movement = self.create_movement()
        user = self.create_user()
        with freeze_time("2023-02-25 19:00:00"):
            message = "Hello, this is a new announcement"
            announcement = Announcement(movement, message, user)
        self.session.add(announcement)
        self.session.commit()

        announcement_json = announcement.to_json()
        json = {'foo': 1, 'bar': ['arr']}
        base_json = json.copy()
        add_json_announcement_details(json, movement, self.session)

        # assert json == json | base_json
        self.assertEqual(json, {**json, **base_json})
        self.assertDictEqual(json['last_announcement'], announcement_json)


class TestUserStoriesAnnouncementController(BaseTest):
    """Announcement user stories."""

    def test_make_movement_announcements(self):
        """
        As an admin I would like to be able to make movement announcements.

        Register an admin, create a movement, create an announcment, then
        getting the movement details should show an announcement.
        """
        email = 'antonin.thioux@gmail.com'
        password = 'password123'
        register('Antonin', email, password, True)
        antonin_id = verify_password_for_email(email, password)

        with freeze_time("2023-02-25 12:00:00"):
            title_1 = "Meditate everyday"
            create_1_json = new_movement_by_user(antonin_id, title_1, 'daily')
            movement_1_json = create_1_json['movement']
            title_2 = "Run once a week"
            create_2_json = new_movement_by_user(antonin_id, title_2, 'weekly')
            movement_2_json = create_2_json['movement']

        m1_id, m2_id = movement_1_json['id'], movement_2_json['id']

        with freeze_time("2023-02-26 11:00:00"):
            message_1 = "Welcome to the meditate everyday movement! Namaste."
            a1_json = create_announcement(message_1, m1_id, antonin_id)

        movement_1_json = get_movement(m1_id, antonin_id)
        self.assertDictEqual(a1_json, movement_1_json['last_announcement'])
        movement_2_json = get_movement(m2_id, antonin_id)
        self.assertIsNone(movement_2_json['last_announcement'])

        with freeze_time("2023-02-26 12:00:00"):
            message_2 = "Welcome to run once a week movement!"
            a2_json = create_announcement(message_2, m2_id, antonin_id)
            message_3 = (
                "New research shows that only 17 minutes of mediation a day "
                "gives benefits"
            )
            a3_json = create_announcement(message_3, m1_id, antonin_id)

        movement_1_json = get_movement(m1_id, antonin_id)
        self.assertDictEqual(a3_json, movement_1_json['last_announcement'])
        movement_2_json = get_movement(m2_id, antonin_id)
        self.assertDictEqual(a2_json, movement_2_json['last_announcement'])

        self.assertEqual(3, self.session.query(Announcement).filter(
            Announcement.poster_id == antonin_id
        ).count())

    def test_update_movement_announcements(self):
        """
        As an administrator I would like to be able to update announcements.

        Register an admin, create a movement, create an announcment, then
        update said announcement should update the announcement.
        """
        email = 'antonin.thioux@gmail.com'
        password = 'password123'
        register('Antonin', email, password, True)
        antonin_id = verify_password_for_email(email, password)
        antonin_json = get_identity(antonin_id)
        del antonin_json['email']  # Email should be private

        with freeze_time("2023-02-25 12:00:00"):
            title = "Floss daily"
            create_json = new_movement_by_user(antonin_id, title, 'daily')
            movement_json = create_json['movement']

        m_id = movement_json['id']

        with freeze_time("2023-02-25 13:00:00"):
            welcome_message = "Welcome to the new movement!"
            welcome_announcement_json = create_announcement(
                welcome_message, m_id, antonin_id
            )
            welcome_id = welcome_announcement_json['id']
        with freeze_time("2023-02-25 13:30:00"):
            info_message = "Find out more information on flossing"
            info_announcement_json = create_announcement(
                info_message, m_id, antonin_id
            )
            info_id = info_announcement_json['id']
        with freeze_time("2023-02-25 15:00:00"):
            welcome_message += "\nFollow us on FaceBook!"
            update_announcement(welcome_message, welcome_id, antonin_id)

        expected_welcome_json = {
            'id': welcome_id,
            'movement_id': m_id,
            'message': welcome_message,
            'poster': antonin_json,
            'created_time': str(datetime(2023, 2, 25, 13, 0).astimezone()),
            'updated_time': str(datetime(2023, 2, 25, 15, 0).astimezone())
        }
        self.assertEqual(
            expected_welcome_json,
            self.session.query(Announcement).filter(
                Announcement.id == welcome_id
            ).one().to_json()
        )
        self.assertEqual(
            info_announcement_json,
            self.session.query(Announcement).filter(
                Announcement.id == info_id
            ).one().to_json()
        )

        with freeze_time("2023-02-26 14:00:00"):
            habit_message = (
                "motivation is what gets you started."
                " habit is what keeps you going"
            )
            habit_announcement_json = create_announcement(
                habit_message, m_id, antonin_id
            )
            habit_id = habit_announcement_json['id']
        with freeze_time("2023-02-26 14:05:00"):
            habit_message = (
                "Motivation is what gets you started,"
                " habit is what keeps you going"
            )
            update_announcement(habit_message, habit_id, antonin_id)
            update_announcement(habit_message + "!", habit_id, antonin_id)
            info_message += " on our facebook page!"
            update_announcement(info_message, info_id, antonin_id)

        expected_info_json = {
            'id': info_id,
            'movement_id': m_id,
            'message': info_message,
            'poster': antonin_json,
            'created_time': str(datetime(2023, 2, 25, 13, 30).astimezone()),
            'updated_time': str(datetime(2023, 2, 26, 14, 5).astimezone())
        }
        expected_habit_json = {
            'id': habit_id,
            'movement_id': m_id,
            'message': habit_message + "!",
            'poster': antonin_json,
            'created_time': str(datetime(2023, 2, 26, 14, 0).astimezone()),
            'updated_time': str(datetime(2023, 2, 26, 14, 5).astimezone())
        }
        self.assertDictEqual(
            expected_welcome_json,
            self.session.query(Announcement).filter(
                Announcement.id == welcome_id
            ).one().to_json()
        )
        self.assertDictEqual(
            expected_info_json,
            self.session.query(Announcement).filter(
                Announcement.id == info_id
            ).one().to_json()
        )
        self.assertDictEqual(
            expected_habit_json,
            self.session.query(Announcement).filter(
                Announcement.id == habit_id
            ).one().to_json()
        )

    def test_delete_movement_announcements(self):
        """
        As an administrator I would like to be able to delete announcements.

        Register an admin, create a movement, create an announcment, then
        delete said announcement should delete the announcement.
        """
        email = 'antonin.thioux@gmail.com'
        password = 'password123'
        register('Antonin', email, password, True)
        antonin_id = verify_password_for_email(email, password)

        with freeze_time("2023-02-25 12:00:00"):
            title_1 = "Floss daily"
            create_1_json = new_movement_by_user(antonin_id, title_1, 'daily')
            movement_1_json = create_1_json['movement']
            title_2 = "Run once a week"
            create_2_json = new_movement_by_user(antonin_id, title_2, 'weekly')
            movement_2_json = create_2_json['movement']

        m1_id, m2_id = movement_1_json['id'], movement_2_json['id']

        with freeze_time("2023-02-25 13:00:00"):
            welcome_message = "Welcome to the new movement!"
            welcome1_announcement_json = create_announcement(
                welcome_message, m1_id, antonin_id
            )
            welcome2_announcement_json = create_announcement(
                welcome_message, m2_id, antonin_id
            )
            welcome1_id = welcome1_announcement_json['id']

        with freeze_time("2023-02-25 14:00:00"):
            wrong_chat_message = "We can use chatGPT to write the assignment"
            wrong_announcement_json = create_announcement(
                wrong_chat_message, m1_id, antonin_id
            )
            wrong_id = wrong_announcement_json['id']

        with freeze_time("2023-02-26 14:30:00"):
            delete_announcement(welcome1_id, antonin_id)
            delete_announcement(wrong_id, antonin_id)

        self.assertIsNone(get_movement(m1_id, antonin_id)['last_announcement'])
        self.assertListEqual([], get_announcements(m1_id))
        self.assertDictEqual(
            welcome2_announcement_json,
            get_movement(m2_id, antonin_id)['last_announcement']
        )
        self.assertListEqual(
            [welcome2_announcement_json],
            get_announcements(m2_id)
        )

    def test_view_announcements(self):
        """As a subscriber I would like to see movement's announcements."""
        email = 'antonin.thioux@gmail.com'
        password = 'password123'
        register('Antonin', email, password, True)
        antonin_id = verify_password_for_email(email, password)

        with freeze_time("2023-02-25 12:00:00"):
            title_1 = "Meditate everyday"
            create_1_json = new_movement_by_user(antonin_id, title_1, 'daily')
            movement_1_json = create_1_json['movement']
            title_2 = "Run once a week"
            create_2_json = new_movement_by_user(antonin_id, title_2, 'weekly')
            movement_2_json = create_2_json['movement']

        m1_id, m2_id = movement_1_json['id'], movement_2_json['id']

        with freeze_time("2023-02-26 11:00:00"):
            message = "Welcome to the meditate everyday movement! Namaste."
            a1_json = create_announcement(message, m1_id, antonin_id)
        with freeze_time("2023-02-26 14:00:00"):
            message = "Find out which meditation practice works best for you"
            a2_json = create_announcement(message, m1_id, antonin_id)
        with freeze_time("2023-02-26 15:00:00"):
            message = "Watch our HD meditation videos on YouTube!"
            a3_json = create_announcement(message, m1_id, antonin_id)
        with freeze_time("2023-02-26 16:00:00"):
            message = "Happiness comes from within, Buy our new merch!"
            a4_json = create_announcement(message, m1_id, antonin_id)

        self.assertListEqual(
            [a4_json, a3_json, a2_json, a1_json],
            get_announcements(m1_id)
        )
        self.assertDictEqual(
            a4_json,
            get_movement(m1_id, antonin_id)['last_announcement']
        )
        self.assertListEqual([], get_announcements(m2_id))
        self.assertIsNone(get_movement(m2_id, antonin_id)['last_announcement'])
