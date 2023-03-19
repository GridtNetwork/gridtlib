"""Test for subscription controller."""
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
    """Subscription controller unittests."""

    def test_helper_get_subscription(self):
        """Unittest _get_subscription."""
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
        """Unittest for _subscription_exists."""
        user = self.create_user()
        movement = self.create_movement()
        self.session.commit()

        user_id = user.id
        movement_id = movement.id

        self.assertFalse(_subscription_exists(
            user_id=user_id,
            movement_id=movement_id,
            session=self.session
        ))

        subscription = Subscription(user, movement)
        self.session.add(subscription)

        self.assertTrue(_subscription_exists(
            user_id=user_id,
            movement_id=movement_id,
            session=self.session
        ))

        subscription.unsubscribe()
        self.session.add(subscription)

        self.assertFalse(_subscription_exists(
            user_id=user_id,
            movement_id=movement_id,
            session=self.session
        ))

    def test_new_subscription(self):
        """Unittest for new_subscription."""
        user = self.create_user()
        movement = self.create_movement()

        self.session.commit()

        user_id = user.id
        movement_id = movement.id
        assert_json_user = user.to_json()
        assert_json_movement = movement.to_json()

        json_subscription = new_subscription(user_id, movement_id)
        self.assertDictEqual(assert_json_user, json_subscription['user'])
        self.assertDictEqual(
            assert_json_movement, json_subscription['movement']
        )
        self.assertTrue(json_subscription['subscribed'])

    def test_remove_subscription(self):
        """Unittest for remove_subscription."""
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
        self.assertDictEqual(
            assert_json_movement, json_subscription['movement']
        )
        self.assertFalse(json_subscription['subscribed'])

        # Test trying to remove none existing subscription
        with self.assertRaises(E.SubscriptionNotFoundError):
            remove_subscription(user_2_id, movement_id)

    def test_get_subscribers_empty(self):
        """Unittest for get_subscribers in empty movement."""
        m1 = self.create_movement()
        self.session.commit()

        movement_id = m1.id
        self.assertListEqual([], get_subscribers(movement_id))

    def test_get_subscribers_one(self):
        """Unittest for get_subscribers in movement with one."""
        m2 = self.create_movement()
        u1 = self.create_user()
        s1 = Subscription(u1, m2)
        self.session.add(s1)
        self.session.commit()

        movement_id = m2.id
        self.assertListEqual([u1.to_json()], get_subscribers(movement_id))

    def test_get_subscribers_multi(self):
        """Unittest for get_subscribers in a movement with multiple peoples."""
        m3 = self.create_movement()
        u1 = self.create_user()
        u2 = self.create_user()
        u3 = self.create_user()
        _ = self.create_user()
        s1 = Subscription(u1, m3)
        s2 = Subscription(u2, m3)
        s3 = Subscription(u3, m3)
        self.session.add_all([s1, s2, s3])
        assert_subscribers = [u1.to_json(), u2.to_json(), u3.to_json()]
        self.session.commit()

        movement_id = m3.id
        subscribers = get_subscribers(movement_id)
        for json_user in assert_subscribers:
            self.assertIn(json_user, subscribers)
        self.assertEqual(3, len(subscribers))

    def test_get_subscriptions(self):
        """Unittest for get_subscriptions."""
        # User 1 isn't subscribed to anything yet
        u1 = self.create_user()

        # User 2 is subscribed to two movements
        u2 = self.create_user()
        m1 = self.create_movement()
        m2 = self.create_movement()
        s1 = Subscription(u2, m1)
        s2 = Subscription(u2, m2)
        self.session.add_all([s1, s2])
        user_id_1, user_id_2 = u1.id, u2.id
        self.session.commit()

        self.assertListEqual([], get_subscriptions(user_id_1))
        self.assertEqual(2, len(get_subscriptions(user_id_2)))


class SubscriptionControllerIntergrationTests(BaseTest):
    """Test for User stories related to subscriptions."""

    def test_subscriptions(self):
        """As a user I want to be about to subscribe to a movement."""
        movement_1 = self.create_movement()
        movement_2 = self.create_movement()

        self.session.commit()
        movement_1_id = movement_1.id
        movement_2_id = movement_2.id

        email_1 = 'antonin.thioux@gmail.com'
        email_2 = 'andrei.dumi20@gmail.com'
        password = 'password123'
        register('Antonin', email_1, 'password123')
        antonin_id = verify_password_for_email(email_1, password)
        antonin_json = get_identity(antonin_id)
        del antonin_json['email']  # Email should be private
        register('Andrei', email_2, password)
        andrei_id = verify_password_for_email(email_2, password)
        andrei_json = get_identity(andrei_id)
        del andrei_json['email']

        ealier = datetime(2023, 1, 6, 9, 0)
        later = datetime(2023, 1, 6, 9, 30)
        with freeze_time(ealier):
            json_1 = new_subscription(antonin_id, movement_1_id)
        with freeze_time(later):
            json_2 = new_subscription(andrei_id, movement_1_id)

        self.assertDictEqual(
            json_1['user'],
            antonin_json,
            "Note that the email should be private"
        )
        self.assertEqual(json_1['time_started'], str(ealier.astimezone()))
        self.assertTrue(json_1['subscribed'])
        self.assertDictEqual(json_2['user'], andrei_json)
        self.assertEqual(json_2['time_started'], str(later.astimezone()))

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
        ).count(), 1, "I would like a follower when I join")

        self.assertEqual(self.session.query(UserToUserLink).filter(
            UserToUserLink.follower_id == andrei_id,
            UserToUserLink.movement_id == movement_1_id,
            UserToUserLink.leader_id == antonin_id,
            UserToUserLink.destroyed.is_(None),
        ).count(), 1, "I would like a leader when I join")

    def test_unsubscribed(self):
        """As a user I would like to be able to unsubscribe from a movement."""
        movement = self.create_movement()
        self.session.commit()
        movement_id = movement.id

        email = 'antonin.thioux@gmail.com'
        password = 'password123'
        register('Antonin', email, password)
        antonin_id = verify_password_for_email(email, password)
        antonin_json = get_identity(antonin_id)
        del antonin_json['email']  # Email should be private

        ealier = datetime(2023, 1, 6, 9, 0)
        later = datetime(2023, 1, 6, 10, 0)
        with freeze_time(ealier):
            json1 = new_subscription(antonin_id, movement_id)

        self.assertDictEqual(json1['user'], antonin_json)
        self.assertEqual(json1['time_started'], str(ealier.astimezone()))
        self.assertTrue(json1['subscribed'])
        self.assertTrue(is_subscribed(antonin_id, movement_id))

        with freeze_time(later):
            json2 = remove_subscription(antonin_id, movement_id)

        self.assertDictEqual(json2['user'], antonin_json)
        self.assertEqual(json2['time_started'], str(ealier.astimezone()))
        self.assertFalse(json2['subscribed'])

        self.assertFalse(is_subscribed(antonin_id, movement_id))
        self.assertNotIn(antonin_json, get_subscribers(movement_id))
        self.assertListEqual([], get_subscriptions(antonin_id))
