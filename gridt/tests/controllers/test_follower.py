from freezegun import freeze_time
from unittest.mock import patch
from gridt.tests.basetest import BaseTest
from gridt.controllers.helpers import leaders
from gridt.models import User, Movement, MovementUserAssociation as MUA
from gridt.controllers.follower import swap_leader, get_leader
from gridt.controllers.leader import send_signal


class GetLeaderTest(BaseTest):
    @patch(
        "gridt.controllers.follower.User.get_email_hash",
        return_value="email_hash",
    )
    def test_get_leader(self, avatar_func):
        """
        movement1:
            l2 <- f -> l1
        movement2:
            l2 -> 1 -> l1
        """
        follower = self.create_user()
        leader1 = self.create_user()
        leader2 = self.create_user()
        movement1 = self.create_movement()
        movement2 = self.create_movement()
        self.session.add_all(
            [
                MUA(movement1, follower, leader1),
                MUA(movement1, follower, leader2),
                MUA(movement2, follower, leader1),
                MUA(movement2, leader2, follower),
            ]
        )
        self.session.commit()

        l1_id = leader1.id
        l1_name = leader1.username
        l2_id = leader2.id
        f_id = follower.id
        m1_id = movement1.id
        m2_id = movement2.id

        with freeze_time("1995-01-15 12:00:00+01:00", tz_offset=1):
            send_signal(l1_id, m1_id, "Message1")
            send_signal(l1_id, m2_id, "Message2")
            send_signal(l2_id, m1_id, "Message3")
        with freeze_time("1996-03-15 12:00:00+01:00", tz_offset=1):
            send_signal(l1_id, m1_id, "Message4")

        leader = get_leader(f_id, m1_id, l1_id)
        self.assertEqual(
            leader,
            {
                "id": l1_id,
                "bio": "",
                "avatar": "email_hash",
                "username": l1_name,
                "message_history": [
                    {
                        "message": "Message4",
                        "time_stamp": "1996-03-15 12:00:00+01:00",
                    },
                    {
                        "message": "Message1",
                        "time_stamp": "1995-01-15 12:00:00+01:00",
                    },
                ],
            },
        )


class SwapTest(BaseTest):
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

        assoc1 = MUA(movement, user1, user2)
        assoc2 = MUA(movement, user2, user1)
        self.session.commit()

        self.assertFalse(swap_leader(user1.id, movement.id, user2.id))
        self.session.add_all([user1, user2, user3, movement])

        user4 = User("user4", "test4@test.com", "password")
        user5 = User("user5", "test5@test.com", "password")
        assoc3 = MUA(movement, user4, None)
        assoc4 = MUA(movement, user5, None)
        self.session.add_all([user1, user2, user3, movement])
        self.session.add_all([user4, user5, assoc1, assoc2, assoc3, assoc4])
        self.session.commit()

        user4_dict = user4.to_json()
        user5_dict = user5.to_json()

        # Will not catch possible mistake:
        #   (movement.swap_leader(gridt., gridt.) == user3)
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

        assoc1 = MUA(movement1, user1, user2)
        assoc2 = MUA(movement1, user2, user1)
        assoc3 = MUA(movement1, user3, user1)
        assoc4 = MUA(movement1, user1, user4)
        assoc5 = MUA(movement2, user1, user5)
        assoc6 = MUA(movement2, user5, user1)

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
        self.assertEqual(new_leader, user3.to_json())

        self.session.add_all([user1, movement2, user5])
        self.assertIsNone(swap_leader(user1.id, movement2.id, user5.id))
