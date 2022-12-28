from ..basetest import BaseTest
from unittest import skip

from gridt.controllers.subscription import (
    _get_subscription,
    is_subscribed,
    get_subscribers,
    get_subscriptions,
    new_subscription,
    remove_subscription
)
import gridt.exc as E
from gridt.models.subscription import Subscription


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

    def test_is_subscribed(self):
        user = self.create_user()
        movement = self.create_movement() 
        self.session.commit()

        user_id = user.id
        movement_id = movement.id

        self.assertFalse(is_subscribed(user_id, movement_id))

        subscription = Subscription(user, movement)
        self.session.add(subscription)

        self.assertTrue(is_subscribed(user_id, movement_id))

        subscription.unsubscribe()
        self.session.add(subscription)

        self.assertFalse(is_subscribed(user_id, movement_id))

    def test_new_subscription(self):
        # I don't test other stuff because it will be moved
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

        # TODO: Test that a message is emitted

    def test_remove_subscription(self):
        # I don't test other stuff because it will moved
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
            _get_subscription(user_2_id, movement_id, self.session)

        # TODO: Test that a message is emitted

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
