from datetime import datetime
from freezegun import freeze_time
from gridt.basetest import BaseTest
from .helpers import leaders
from .movements import subscribe, remove_user_from_movement
from gridt.models import User, Movement, MovementUserAssociation


class TestMovements(BaseTest):
    def test_subscribe(self):
        user1 = User("user1", "test1@test.com", "pass")
        user2 = User("user2", "test2@test.com", "pass")
        user3 = User("user3", "test3@test.com", "pass")
        movement1 = Movement("movement1", "daily")
        movement2 = Movement("movement2", "twice daily")

        self.session.add_all([user1, user2, user3, movement1, movement2])
        self.session.commit()

        self.assertEqual(user1.follower_associations, [])
        self.assertEqual(
            leaders(user1, movement1, self.session).all(), []
        )
        self.assertEqual(user2.follower_associations, [])
        self.assertEqual(
            leaders(user2, movement1, self.session).all(), []
        )
        self.assertEqual(movement1.user_associations, [])
        self.assertEqual(movement2.user_associations, [])

        subscribe(user1.id, movement1.id)
        self.session.add_all([user1, user2, user3, movement1, movement2])

        self.assertEqual(len(user1.follower_associations), 1)
        self.assertEqual(len(user2.follower_associations), 0)
        self.assertEqual(len(movement1.user_associations), 1)
        self.assertEqual(len(movement2.user_associations), 0)
        self.assertEqual(
            leaders(user1, movement1, self.session).all(), []
        )

        subscribe(user2.id, movement1.id)
        self.session.add_all([user1, user2, user3, movement1, movement2])

        self.assertEqual(len(user1.follower_associations), 2)
        self.assertEqual(len(user2.follower_associations), 1)
        self.assertEqual(len(movement1.user_associations), 3)
        self.assertEqual(len(movement2.user_associations), 0)
        self.assertEqual(
            leaders(user1, movement1, self.session).all(), [user2]
        )
        self.assertEqual(
            leaders(user2, movement1, self.session).all(), [user1]
        )

        subscribe(user3.id, movement1.id)
        self.session.add_all([user1, user2, user3, movement1, movement2])

        self.assertEqual(len(user1.follower_associations), 3)
        self.assertEqual(len(user2.follower_associations), 2)
        self.assertEqual(len(user3.follower_associations), 2)
        self.assertEqual(len(movement1.user_associations), 7)
        self.assertEqual(len(movement2.user_associations), 0)
        self.assertEqual(
            set(leaders(user1, movement1, self.session).all()),
            set([user2, user3]),
        )
        self.assertEqual(
            set(leaders(user2, movement1, self.session).all()),
            set([user1, user3]),
        )
        self.assertEqual(
            set(leaders(user3, movement1, self.session).all()),
            set([user1, user2]),
        )

    def test_remove_user(self):
        user1 = User("user1", "test1@test.com", "password")
        movement1 = Movement("movement1", "daily")
        mua1 = MovementUserAssociation(movement1, user1, None)
        self.session.add_all([user1, movement1, mua1])
        self.session.commit()

        with freeze_time("2020-04-18 22:10:00"):
            remove_user_from_movement(user1.id, movement1.id)
        self.session.add_all([user1, movement1, mua1])

        self.assertFalse(user1 in movement1.active_users)
        self.assertFalse(
            movement1 in user1.current_movements
        )

        self.assertEqual(
            len(user1.follower_associations),
            1,
            "Mua must still be present after destruction.",
        )

        self.assertEqual(
            user1.follower_associations[0].destroyed,
            datetime(2020, 4, 18, 22, 10),
            "Mua must be destroyed when user is removed from movement.",
        )
