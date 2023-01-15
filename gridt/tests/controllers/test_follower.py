from freezegun import freeze_time
from unittest.mock import patch
from gridt.tests.basetest import BaseTest
from gridt.models import User, Movement, MovementUserAssociation as MUA
from gridt.models import Subscription as SUB
from gridt.controllers.follower import swap_leader, get_leader, add_initial_leaders, remove_all_leaders, possible_followers, get_leaders
from gridt.controllers.leader import send_signal
from datetime import datetime


class TestLeaderlessFollowers(BaseTest):
    def test_possible_followers(self):
        movement1 = Movement("test1", "daily")
        movement2 = Movement("test2", "daily")

        for i in range(6):
            user = User(f"user{i}", f"user{i}@email.com", "pass")
            self.session.add(user)
        users = self.session.query(User).all()

        muas = [
            MUA(movement1, users[0], users[1]),
            MUA(movement1, users[0], users[2]),
            MUA(movement1, users[0], users[3]),
            MUA(movement1, users[1], users[0]),
            MUA(movement1, users[1], users[2]),
            MUA(movement1, users[1], users[3]),
            MUA(movement1, users[2], users[1]),
            MUA(movement1, users[2], users[5]),
            MUA(movement1, users[2], users[3]),
            MUA(movement1, users[2], users[4]),
            MUA(movement2, users[0], users[1]),
            MUA(movement2, users[0], users[2]),
            MUA(movement2, users[0], users[3]),
        ]

        subs = [
            SUB(users[0], movement1),
            SUB(users[1], movement1),
            SUB(users[2], movement1),
            SUB(users[3], movement1),
            SUB(users[4], movement1),
            SUB(users[5], movement1),
            SUB(users[0], movement2),
            SUB(users[1], movement2),
            SUB(users[2], movement2),
            SUB(users[3], movement2)
        ]

        self.session.add_all(subs)

        self.session.add_all(muas)
        self.session.commit()

        self.assertEqual(
            set(possible_followers(users[0], movement2, self.session)),
            set(users[1:4]),
        )

        self.assertEqual(
            set(possible_followers(users[0], movement1, self.session)),
            set(users[3:]),
        )

        mua1 = self.session.query(MUA).filter(MUA.id == 1).one()
        mua1.destroy()

        self.assertEqual(
            set(possible_followers(users[0], movement1, self.session)),
            set(users[3:]),
        )
        self.assertEqual(
            set(possible_followers(users[0], movement2, self.session)),
            set(users[1:4]),
        )

        mua2 = (
            self.session.query(MUA)
            .filter(
                MUA.follower_id == users[1].id,
                MUA.leader_id == users[2].id,
                MUA.movement_id == movement1.id,
            )
            .one()
        )
        mua2.destroy()

        self.assertEqual(
            set(possible_followers(users[0], movement1, self.session)),
            set([users[3], users[4], users[5]]),
        )
        self.assertEqual(
            set(possible_followers(users[0], movement2, self.session)),
            set(users[1:4]),
        )


class OnSubscriptionEventsFollowerTests(BaseTest):

    def test_add_initial_leaders(self):
        follower = self.create_user()
        u1 = self.create_user()
        u2 = self.create_user()
        u3 = self.create_user()
        u4 = self.create_user()
        u5 = self.create_user()
        mA = self.create_movement()
        mB = self.create_movement()
        mC = self.create_movement()
        mD = self.create_movement()
        mE = self.create_movement()
        self.session.add_all(
            [
                # Movement B
                MUA(mB, u1, None),

                # Movement C
                MUA(mC, u1, u2), MUA(mC, u2, u1),

                # Movement D
                MUA(mD, u1, u2), MUA(mD, u1, u3),
                MUA(mD, u2, u3), MUA(mD, u2, u4),
                MUA(mD, u3, u4), MUA(mD, u3, u5),
                MUA(mD, u4, u5), MUA(mD, u3, u1),
                MUA(mD, u5, u1), MUA(mD, u5, u2),

                # Movement E
                MUA(mE, u1, u2), MUA(mE, u1, u3), MUA(mE, u1, u4), MUA(mE, u1, u5),
                MUA(mE, u2, u3), MUA(mE, u2, u4), MUA(mE, u2, u5), MUA(mE, u2, u1),
                MUA(mE, u3, u4), MUA(mE, u3, u5), MUA(mE, u3, u1), MUA(mE, u3, u2),
                MUA(mE, u4, u5), MUA(mE, u4, u1), MUA(mE, u4, u2), MUA(mE, u4, u3),
                MUA(mE, u5, u1), MUA(mE, u5, u2), MUA(mE, u5, u3), MUA(mE, u5, u4)
            ]
        )
        self.session.commit()
        follower_id = follower.id
        u1_id = u1.id
        u2_id = u2.id
        u3_id = u3.id
        u4_id = u4.id
        u5_id = u5.id
        mA_id = mA.id
        mB_id = mB.id
        mC_id = mC.id
        mD_id = mD.id
        mE_id = mE.id

        # Test 0 users in movement A
        add_initial_leaders(follower_id, mA_id)
        self.assertEqual(self.session.query(MUA).filter(MUA.movement_id == mA_id).count(), 1)
        self.assertEqual(self.session.query(MUA).filter(
            MUA.follower_id == follower_id,
            MUA.movement_id == mA_id,
            MUA.leader_id.is_(None),
            MUA.destroyed.is_(None),
        ).count(), 1)

        # Test 1 user in movement B
        add_initial_leaders(follower_id, mB_id)
        self.assertEqual(self.session.query(MUA).filter(
            MUA.movement_id == mB_id,
            MUA.follower_id == follower_id
        ).count(), 1)
        self.assertEqual(self.session.query(MUA).filter(
            MUA.follower_id == follower_id,
            MUA.movement_id == mB_id,
            MUA.leader_id == u1_id,
            MUA.destroyed.is_(None),
        ).count(), 1)

        # Test 2 users in movement C
        add_initial_leaders(follower_id, mC_id)
        self.assertEqual(self.session.query(MUA).filter(
            MUA.follower_id == follower_id,
            MUA.movement_id == mC_id,
            MUA.destroyed.is_(None),
        ).count(), 2)
        self.assertEqual(self.session.query(MUA).filter(
            MUA.follower_id == follower_id,
            MUA.leader_id == u1_id,
            MUA.movement_id == mC_id,
            MUA.destroyed.is_(None),
        ).count(), 1)
        self.assertEqual(self.session.query(MUA).filter(
            MUA.follower_id == follower_id,
            MUA.leader_id == u2_id,
            MUA.movement_id == mC_id,
            MUA.destroyed.is_(None),
        ).count(), 1)

        # Test 5 users in movement D
        add_initial_leaders(follower_id, mD_id)
        self.assertEqual(self.session.query(MUA).filter(
            MUA.follower_id == follower_id,
            MUA.leader_id.in_([u1_id, u2_id, u3_id, u4_id, u5_id]),
            MUA.movement_id == mD_id,
            MUA.destroyed.is_(None),
        ).count(), 4)

        # Test 5 users in movement E but all leaders have 4 followers
        add_initial_leaders(follower_id, mE_id)
        self.assertEqual(self.session.query(MUA).filter(
            MUA.follower_id == follower_id,
            MUA.leader_id.in_([u1_id, u2_id, u3_id, u4_id, u5_id]),
            MUA.movement_id == mE_id,
            MUA.destroyed.is_(None),
        ).count(), 4)

    def test_remove_all_leaders(self):
        follower = self.create_user()
        u1 = self.create_user()
        u2 = self.create_user()
        u3 = self.create_user()
        mA = self.create_movement()
        mB = self.create_movement()
        mC = self.create_movement()
        mD = self.create_movement()
        mE = self.create_movement()
        self.session.add_all(
            [
                # Movement A
                SUB(follower, mA),

                # Movement B
                MUA(mB, follower, u1),
                SUB(follower, mB),
                SUB(u1, mB),

                # Movement C
                MUA(mC, follower, u1), MUA(mC, follower, u2),
                SUB(follower, mC),
                SUB(u1, mC),
                SUB(u2, mC),

                # Movement D
                MUA(mD, follower, u1),
                MUA(mD, follower, u2),
                MUA(mD, follower, u3),
                MUA(mD, u1, u2),
                MUA(mD, u2, u3),
                MUA(mD, u3, u1),
                SUB(follower, mD),
                SUB(u1, mD),
                SUB(u2, mD),
                SUB(u3, mD),

                # Movement E
                MUA(mE, u1, u2),
                MUA(mE, u2, u3),
                MUA(mE, u3, u1),
                MUA(mE, u2, u1),
                MUA(mE, u3, u2),
                MUA(mE, u1, u3),
                SUB(u1, mE),
                SUB(u2, mE),
                SUB(u3, mE),
            ]
        )


        self.session.commit()
        follower_id = follower.id
        u1_id = u1.id
        u2_id = u2.id
        u3_id = u3.id
        mA_id = mA.id
        mB_id = mB.id
        mC_id = mC.id
        mD_id = mD.id
        mE_id = mE.id

        # Test 0 users in movement A
        with freeze_time("2023-01-03 00:00:00+01:00"):
            remove_all_leaders(follower_id, mA_id)
        self.assertEqual(self.session.query(MUA).filter(
            MUA.follower_id == follower_id,
            MUA.movement_id == mA_id,
            MUA.destroyed == datetime(2023, 1, 2, 23, 0),
        ).count(), 0)

        # Test 1 user in movement B
        with freeze_time("2023-01-03 00:00:00+01:00"):
            remove_all_leaders(follower_id, mB_id)
        self.assertEqual(self.session.query(MUA).filter(
            MUA.follower_id == follower_id,
            MUA.leader_id == u1_id,
            MUA.movement_id == mB_id,
            MUA.destroyed == datetime(2023, 1, 2, 23, 0),
        ).count(), 1)
        self.assertEqual(self.session.query(MUA).filter(
            MUA.movement_id == mB_id,
            MUA.destroyed.is_(None)
        ).count(), 0)

        # Test 2 users in movement C
        with freeze_time("2023-01-03 00:00:00+01:00"):
            remove_all_leaders(follower_id, mC_id)
        self.assertEqual(self.session.query(MUA).filter(
            MUA.follower_id == follower_id,
            MUA.movement_id == mC_id,
            MUA.destroyed == datetime(2023, 1, 2, 23, 0)
        ).count(), 2)
        self.assertEqual(self.session.query(MUA).filter(
            MUA.movement_id == mC_id,
            MUA.destroyed.is_(None)
        ).count(), 2)

        # Test 3 users in movement D
        with freeze_time("2023-01-03 00:00:00+01:00"):
            remove_all_leaders(follower_id, mD_id)
        self.assertEqual(self.session.query(MUA).filter(
            MUA.follower_id == follower_id,
            MUA.movement_id == mD_id,
            MUA.destroyed == datetime(2023, 1, 2, 23, 0)
        ).count(), 3)
        self.assertEqual(self.session.query(MUA).filter(
            MUA.follower_id == u1_id,
            MUA.movement_id == mD_id,
            MUA.destroyed.is_(None)
        ).count(), 2)
        self.assertEqual(self.session.query(MUA).filter(
            MUA.follower_id == u2_id,
            MUA.movement_id == mD_id,
            MUA.destroyed.is_(None)
        ).count(), 2)
        self.assertEqual(self.session.query(MUA).filter(
            MUA.follower_id == u3_id,
            MUA.movement_id == mD_id,
            MUA.destroyed.is_(None)
        ).count(), 2)

        # Test 3 users in movement E (follower not in movement)
        with freeze_time("2023-01-03 00:00:00+01:00"):
            remove_all_leaders(follower_id, mE_id)
        self.assertEqual(self.session.query(MUA).filter(
            MUA.movement_id == mE_id,
            MUA.destroyed.is_(None)
        ).count(), 6)
  
        
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
        self.create_subscription(movement=movement1, user=follower)
        self.create_subscription(movement=movement1, user=leader1)
        self.create_subscription(movement=movement1, user=leader2)
        self.create_subscription(movement=movement2, user=follower)
        self.create_subscription(movement=movement2, user=leader1)
        self.create_subscription(movement=movement2, user=leader2)
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
        self.assertEqual(len(get_leaders(user2, movement, self.session)), 1)

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


class TestGetLeaders(BaseTest):
    def test_get_leaders(self):
        """
        movement1:
            3 <- 1 -> 2 -> 4
        """
        user1 = User("user1", "test1@test.com", "test")
        user2 = User("user2", "test2@test.com", "test")
        user3 = User("user3", "test3@test.com", "test")
        user4 = User("user4", "test4@test.com", "test")

        movement = Movement("movement1", "daily")

        assoc1 = MUA(movement, user1, user2)
        assoc2 = MUA(movement, user1, user3)
        assoc3 = MUA(movement, user2, user4)

        self.session.add_all([user1, user2, user3, assoc1, assoc2, assoc3])
        self.session.commit()

        self.assertEqual(len(get_leaders(user1, movement, self.session)), 2)
        self.assertEqual(
            set(get_leaders(user1, movement, self.session)),
            set([user2, user3]),
        )

    def test_get_leaders_removed(self):
        """
        movement1:
            3 <- 1 -> 2
                 |
                 v
                 4
        """
        user1 = User("user1", "test1@test.com", "test")
        user2 = User("user2", "test2@test.com", "test")
        user3 = User("user3", "test3@test.com", "test")
        user4 = User("user4", "test4@test.com", "test")

        movement = Movement("movement1", "daily")

        assoc1 = MUA(movement, user1, user2)
        assoc2 = MUA(movement, user1, user3)
        assoc3 = MUA(movement, user1, user4)
        assoc3.destroy()

        self.session.add_all(
            [user1, user2, user3, user4, assoc1, assoc2, assoc3]
        )
        self.session.commit()

        self.assertEqual(len(get_leaders(user1, movement, self.session)), 2)
        self.assertEqual(
            set(get_leaders(movement, user1, self.session)),
            set([user2, user3]),
        )
