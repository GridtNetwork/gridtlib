from gridt.tests.basetest import BaseTest
from gridt.models import Subscription, User, Movement
from freezegun import freeze_time
from datetime import datetime



class UnitTestSubscription(BaseTest):

    def test_init(self):
        with freeze_time('2022-12-27 03:10:00'):
            subscription1 = Subscription()

        self.assertIsNone(subscription1.movement)
        self.assertIsNone(subscription1.user)
        self.assertEqual(subscription1.time_added, datetime(2022,12,27,3,10,00))
        self.assertEqual(subscription1.type, 'subscription')

        user = self.create_user()
        movement = self.create_movement()

        with freeze_time('2022-12-27 01:54:00'):
            subscription2 = Subscription(user, movement)
        
        self.assertEqual(subscription2.movement, movement)    
        self.assertEqual(subscription2.user, user)    
        self.assertEqual(subscription2.time_added, datetime(2022,12,27,1,54,00))
        self.assertEqual(subscription2.type, 'subscription')


    def test_unsubscribe(self):
        user = self.create_user()
        movement = self.create_movement()
        subscription = Subscription(user, movement)

        with freeze_time('2022-12-27 01:54:00'):
            subscription.unsubscribe()

        self.assertEqual(subscription.time_removed, datetime(2022,12,27,1,54,00))
        self.assertTrue(subscription.has_ended())


    def test_repr(self):
        user = User("abc123", "test@test.com", "password")
        movement = Movement("xyz890", "weekly", "some movement")
        subscription = Subscription(user, movement)
        self.assertEqual(
            str(subscription),
            '<Subscription relation: abc123 is subscribed to xyz890>'
        )


