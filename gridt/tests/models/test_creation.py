from gridt.tests.basetest import BaseTest
from gridt.models import Creation, User, Movement
from freezegun import freeze_time
from datetime import datetime


class UnitTestCreation(BaseTest):
    def test_init(self):
        creation1 = None
        with freeze_time('2022-12-27 03:36:00'):
            creation1 = Creation()

        self.assertIsNone(creation1.movement)
        self.assertIsNone(creation1.user)
        self.assertEqual(creation1.time_added, datetime(2022,12,27,3,36,00))
        self.assertEqual(creation1.type, 'creation')

        user = self.create_user()
        movement = self.create_movement()

        creation2 = None
        with freeze_time('2022-12-27 03:36:00'):
            creation2 = Creation(user, movement)
        
        self.assertEqual(creation2.movement, movement)
        self.assertEqual(creation2.user, user)
        self.assertEqual(creation2.time_added, datetime(2022,12,27,3,36,00))
        self.assertEqual(creation2.type, 'creation')


    def test_end(self):
        user = self.create_user()
        movement = self.create_movement()
        creation = Creation(user, movement)

        with freeze_time('2022-12-27 03:36:00'):
            creation.end()

        self.assertEqual(creation.time_removed, datetime(2022,12,27,3,36,00))
        self.assertTrue(creation.is_ended())


    def test_repr(self):
        user = User("abc123", "test@test.com", "password")
        movement = Movement("xyz890", "weekly", "some movement")
        creation = Creation(user, movement)
        self.assertEqual(
            str(creation),
            '<Creation relation: abc123 has created xyz890>'
        )


