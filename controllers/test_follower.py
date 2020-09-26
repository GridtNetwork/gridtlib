import unittest
from .basetest import BaseTest
from .helpers import leaders
from models import User, Movement, MovementUserAssociation
from .follower import swap_leader


class FollowerIntegrationTest(BaseTest):
    @unittest.skip
    def test_get_subscriptions(self):
        pass

    def test_swap(self):
        """
        movement1:
            1 <-> 2 4 5
        """
        user1 = User("user1", "test1@test.com", "password")
        user2 = User("user2", "test2@test.com", "password")
        user3 = User("user3", "test3@test.com", "password")
        movement = Movement("movement1", "daily")

        self.session.add_all([user1, user2, user3, movement])
        self.session.commit()

        assoc1 = MovementUserAssociation(movement, user1, user2)
        assoc2 = MovementUserAssociation(movement, user2, user1)
        self.session.commit()

        self.assertFalse(swap_leader(user1.id, movement.id, user2.id))
        self.session.add_all([user1, user2, user3, movement])

        user4 = User("user4", "test4@test.com", "password")
        user5 = User("user5", "test5@test.com", "password")
        assoc3 = MovementUserAssociation(movement, user4, None)
        assoc4 = MovementUserAssociation(movement, user5, None)
        self.session.add_all([user1, user2, user3, movement])
        self.session.add_all([user4, user5, assoc1, assoc2, assoc3, assoc4])
        self.session.commit()

        # Will not catch possible mistake:
        #   (movement.swap_leader(..., ...) == user3)
        # 2/3 of the time
        self.assertIn(
            swap_leader(user2.id, movement.id, user1.id), [user4, user5]
        )
        self.session.add_all([user1, user2, user3, movement])
        self.session.add_all([user4, user5, assoc1, assoc2, assoc3, assoc4])
        self.assertEqual(leaders(user2, movement, self.session).count(), 1)
