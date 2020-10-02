import unittest
from gridt.basetest import BaseTest
from .helpers import leaders
from gridt.models import User, Movement, MovementUserAssociation
from .follower import swap_leader


class FollowerIntegrationTest(BaseTest):
    @unittest.skip
    def test_get_subscriptions(self):
        pass

    def test_swap(self):
        """
        movement1:
            1 <-> 2 4 5

        TODO: At this point, this does not test the last signal functionality.
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

        user4_dict = user4.dictify()
        user5_dict = user5.dictify()

        # Will not catch possible mistake:
        #   (movement.swap_leader(..., ...) == user3)
        # 2/3 of the time
        self.assertIn(
            swap_leader(user2.id, movement.id, user1.id),
            [user4_dict, user5_dict],
        )
        self.session.add_all([user1, user2, user3, movement])
        self.session.add_all([user4, user5, assoc1, assoc2, assoc3, assoc4])
        self.assertEqual(leaders(user2, movement, self.session).count(), 1)

    def test_swap_leader_complicated(self):
        """
        Movement 1

              3 -> 1 <-> 2
                   |
                   v
                   4

        ------------------------------------------------------
        Movement 2

            1 <-> 5

        """
        user1 = User("user1", "test1@test.com", "password")
        user2 = User("user2", "test2@test.com", "password")
        user3 = User("user3", "test3@test.com", "password")
        user4 = User("user4", "test4@test.com", "password")
        user5 = User("user5", "test5@test.com", "password")
        movement1 = Movement("movement1", "daily")
        movement2 = Movement("movement2", "daily")

        assoc1 = MovementUserAssociation(movement1, user1, user2)
        assoc2 = MovementUserAssociation(movement1, user2, user1)
        assoc3 = MovementUserAssociation(movement1, user3, user1)
        assoc4 = MovementUserAssociation(movement1, user1, user4)
        assoc5 = MovementUserAssociation(movement2, user1, user5)
        assoc6 = MovementUserAssociation(movement2, user5, user1)

        self.session.add_all(
            [
                user1,
                user2,
                user3,
                user4,
                movement1,
                movement2,
                assoc1,
                assoc2,
                assoc3,
                assoc4,
                assoc5,
                assoc6,
            ]
        )
        self.session.commit()

        new_leader = swap_leader(user1.id, movement1.id, user2.id)
        # Make sure that it is actually saved in the database!
        self.session.rollback()
        self.session.add(user3)
        self.assertEqual(new_leader, user3.dictify())

        self.session.add_all([user1, movement2, user5])
        self.assertIsNone(swap_leader(user1.id, movement2.id, user5.id))
