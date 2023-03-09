from ..basetest import BaseTest

from gridt.controllers.subscription import (
    _get_subscription,
    _subscription_exists,
    is_subscribed,
    get_subscribers,
    get_subscriptions,
    new_subscription,
    remove_subscription,
)
from gridt.controllers.user import (
    register,
    verify_password_for_email,
    get_identity
)
import gridt.exc as E
from gridt.models import Subscription, UserToUserLink

from freezegun import freeze_time
from datetime import datetime


class SubscriptionControllerUnitTest(BaseTest):
    
    def test_helper_get_subscription(self):
        user = self.create_user()
        self.session.commit()
        movement = self.create_movement()

        user_id = user.id
        movement_id = movement.id

        # Test when subcription does not exist that an error is raised
        with self.assertRaises(E.SubscriptionNotFoundError):
            _get_subscription(user_id, movement_id, self.session)

        subscription1 = Subscription(user, movement)
        self.session.add(subscription1)

        subscription2 = _get_subscription(user.id, movement.id, self.session)
        self.assertEqual(subscription1.id, subscription2.id)
        self.assertEqual(subscription1.user_id, subscription2.user_id)
        self.assertEqual(subscription1.movement_id, subscription2.movement_id)

    def test_subscription_exists(self):
        user = self.create_user()
        movement = self.create_movement() 
        self.session.commit()

        user_id = user.id
        movement_id = movement.id

        self.assertFalse(_subscription_exists(user_id, movement_id, self.session))

        subscription = Subscription(user, movement)
        self.session.add(subscription)

        self.assertTrue(_subscription_exists(user_id, movement_id, self.session))

        subscription.unsubscribe()
        self.session.add(subscription)

        self.assertFalse(_subscription_exists(user_id, movement_id, self.session))

    def test_new_subscription(self):
        user = self.create_user()
        movement = self.create_movement() 

        self.session.commit()

        user_id = user.id
        movement_id = movement.id
        assert_json_user = user.to_json()
        assert_json_movement = movement.to_json()

        json_subscription = new_subscription(user_id, movement_id)
        self.assertDictEqual(assert_json_user, json_subscription['user'])
        self.assertDictEqual(assert_json_movement, json_subscription['movement'])
        self.assertTrue(json_subscription['subscribed'])

    def test_remove_subscription(self):
        movement = self.create_movement()
        u1 = self.create_user()
        u2 = self.create_user()
        s1 = Subscription(u1, movement)
        self.session.add(s1)

        user_1_id = u1.id
        user_2_id = u2.id
        movement_id = movement.id
        assert_json_user = u1.to_json()
        assert_json_movement = movement.to_json()

        self.session.commit()
        
        # Test removing an existing subscription
        json_subscription = remove_subscription(user_1_id, movement_id)
        self.assertDictEqual(assert_json_user, json_subscription['user'])
        self.assertDictEqual(assert_json_movement, json_subscription['movement'])
        self.assertFalse(json_subscription['subscribed'])

        # Test trying to remove none existing subscription
        with self.assertRaises(E.SubscriptionNotFoundError):
            remove_subscription(user_2_id, movement_id)

    def test_get_subscribers_empty(self):
        m1 = self.create_movement()
        self.session.commit()

        movement_id = m1.id
        self.assertListEqual([], get_subscribers(movement_id))

    def test_get_subscribers_one(self):
        m2 = self.create_movement()
        u1 = self.create_user()
        s1 = Subscription(u1, m2)
        self.session.add(s1)
        self.session.commit()

        movement_id = m2.id
        self.assertListEqual([u1.to_json()], get_subscribers(movement_id))

    def test_get_subscribers_multi(self):
        m3 = self.create_movement()
        u1 = self.create_user()
        u2 = self.create_user()
        u3 = self.create_user()
        _ = self.create_user()
        s1 = Subscription(u1, m3)
        s2 = Subscription(u2, m3)
        s3 = Subscription(u3, m3)
        self.session.add_all([s1,s2,s3])
        assert_subscribers = [u1.to_json(), u2.to_json(), u3.to_json()]
        self.session.commit()

        movement_id = m3.id
        subscribers = get_subscribers(movement_id)
        for json_user in assert_subscribers:
            self.assertIn(json_user, subscribers)
        self.assertEqual(3, len(subscribers))

    def test_get_subscriptions(self):
        # User 1 isn't subscribed to anything yet
        u1 = self.create_user()
        
        # User 2 is subscribed to two movements
        u2 = self.create_user()
        m1 = self.create_movement()
        m2 = self.create_movement()
        s1 = Subscription(u2, m1)
        s2 = Subscription(u2, m2)
        self.session.add_all([s1,s2])
        user_id_1, user_id_2 = u1.id, u2.id
        self.session.commit()

        self.assertListEqual([], get_subscriptions(user_id_1))
        self.assertEqual(2, len(get_subscriptions(user_id_2)))


class SubscriptionControllerIntergrationTests(BaseTest):

    def test_subscriptions(self):
        movement_1 = self.create_movement()
        movement_2 = self.create_movement()

        self.session.commit()
        movement_1_id = movement_1.id
        movement_2_id = movement_2.id

        register('Antonin', 'antonin.thioux@gmail.com', 'password123')
        antonin_id = verify_password_for_email('antonin.thioux@gmail.com', 'password123')
        antonin_json = get_identity(antonin_id)
        del antonin_json['email']  # Email should be private
        register('Andrei', 'andrei.dumi20@gmail.com', 'password123')
        andrei_id = verify_password_for_email('andrei.dumi20@gmail.com', 'password123')
        andrei_json = get_identity(andrei_id)
        del andrei_json['email']

        with freeze_time("2023-01-06 09:00:00"):
            json_1 = new_subscription(antonin_id, movement_1_id)
        with freeze_time("2023-01-06 09:30:00"):
            json_2 = new_subscription(andrei_id, movement_1_id)

        self.assertDictEqual(json_1['user'], antonin_json, 'Note that the email should be private')
        self.assertEqual(json_1['time_started'], str(datetime(2023, 1, 6, 9, 0).astimezone()))
        self.assertTrue(json_1['subscribed'])
        self.assertDictEqual(json_2['user'], andrei_json)
        self.assertEqual(json_2['time_started'], str(datetime(2023, 1, 6, 9, 30).astimezone()))

        self.assertTrue(is_subscribed(antonin_id, movement_1_id))
        self.assertTrue(is_subscribed(andrei_id, movement_1_id))
        self.assertIn(antonin_json, get_subscribers(movement_1_id))
        self.assertIn(andrei_json, get_subscribers(movement_1_id))
        self.assertEqual(get_subscriptions(antonin_id)[0]['id'], movement_1_id)
        self.assertEqual(get_subscriptions(andrei_id)[0]['id'], movement_1_id)
        self.assertFalse(is_subscribed(antonin_id, movement_2_id))
        self.assertNotIn(antonin_json, get_subscribers(movement_2_id))
        self.assertNotIn(andrei_json, get_subscribers(movement_2_id))

        self.assertEqual(self.session.query(UserToUserLink).filter(
            UserToUserLink.follower_id == antonin_id,
            UserToUserLink.movement_id == movement_1_id,
            UserToUserLink.leader_id == andrei_id,
            UserToUserLink.destroyed.is_(None),
        ).count(), 1, "When a user joins a movement followers without leaders should follow them")

        self.assertEqual(self.session.query(UserToUserLink).filter(
            UserToUserLink.follower_id == andrei_id,
            UserToUserLink.movement_id == movement_1_id,
            UserToUserLink.leader_id == antonin_id,
            UserToUserLink.destroyed.is_(None),
        ).count(), 1, "When a user joins a movement they should be given leaders")
    
    def test_unsubscribed(self):
        movement = self.create_movement()
        self.session.commit()
        movement_id = movement.id

        register('Antonin', 'antonin.thioux@gmail.com', 'password123')
        antonin_id = verify_password_for_email('antonin.thioux@gmail.com', 'password123')
        antonin_json = get_identity(antonin_id)
        del antonin_json['email']  # Email should be private

        with freeze_time("2023-01-06 09:00:00"):
            json1 = new_subscription(antonin_id, movement_id)

        self.assertDictEqual(json1['user'], antonin_json)
        self.assertEqual(json1['time_started'], str(datetime(2023, 1, 6, 9, 0).astimezone()))
        self.assertTrue(json1['subscribed'])
        self.assertTrue(is_subscribed(antonin_id, movement_id))

        with freeze_time("2023-01-06 10:00:00"):
            json2 = remove_subscription(antonin_id, movement_id)
        
        self.assertDictEqual(json2['user'], antonin_json)
        self.assertEqual(json2['time_started'], str(datetime(2023, 1, 6, 9, 0).astimezone()))
        self.assertFalse(json2['subscribed'])

        self.assertFalse(is_subscribed(antonin_id, movement_id))
        self.assertNotIn(antonin_json, get_subscribers(movement_id))
        self.assertListEqual([], get_subscriptions(antonin_id))

