from gridt.tests.basetest import BaseTest
from gridt.models import UserToUserLink, Signal, User, Movement
from gridt.controllers.leader import send_signal, _add_initial_followers, _remove_all_followers, possible_leaders
from freezegun import freeze_time
from datetime import datetime


class OnSubscriptionEventsLeaderTests(BaseTest):
    def test_add_initial_followers(self):
        leader = self.create_user()
        u1 = self.create_user()
        u2 = self.create_user()
        u3 = self.create_user()
        u4 = self.create_user()
        u5 = self.create_user()
        mA = self.create_movement()
        mB = self.create_movement()
        self.session.add_all(
            [   
                # Movement A
                UserToUserLink(mA, u1, u2), UserToUserLink(mA, u1, u3),
                UserToUserLink(mA, u2, u3), UserToUserLink(mA, u2, u4),
                UserToUserLink(mA, u3, u4), UserToUserLink(mA, u3, u5),
                UserToUserLink(mA, u4, u5), UserToUserLink(mA, u3, u1),
                UserToUserLink(mA, u5, u1), UserToUserLink(mA, u5, u2),

                # Movement B
                UserToUserLink(mB, u1, u2), UserToUserLink(mB, u1, u3), UserToUserLink(mB, u1, u4), UserToUserLink(mB, u1, u5),
                UserToUserLink(mB, u2, u3), UserToUserLink(mB, u2, u4), UserToUserLink(mB, u2, u5), UserToUserLink(mB, u2, u1),
                UserToUserLink(mB, u3, u4), UserToUserLink(mB, u3, u5), UserToUserLink(mB, u3, u1), UserToUserLink(mB, u3, u2),
                UserToUserLink(mB, u4, u5), UserToUserLink(mB, u4, u1), UserToUserLink(mB, u4, u2), UserToUserLink(mB, u4, u3),
                UserToUserLink(mB, u5, u1), UserToUserLink(mB, u5, u2), UserToUserLink(mB, u5, u3), UserToUserLink(mB, u5, u4)
            ]
        )
        self.session.commit()
        leader_id = leader.id
        u1_id = u1.id
        u2_id = u2.id
        u3_id = u3.id
        u4_id = u4.id
        u5_id = u5.id
        mA_id = mA.id
        mB_id = mB.id

        # Test 5 users in Movement A (partily connected)
        _add_initial_followers(leader_id, mA_id)
        self.assertEqual(self.session.query(UserToUserLink).filter(
            UserToUserLink.leader_id == leader_id,
            UserToUserLink.follower_id.in_([u1_id, u2_id, u3_id, u4_id, u5_id]),
            UserToUserLink.movement_id == mA_id,
            UserToUserLink.destroyed.is_(None),
        ).count(), 5)  # This is 5 because we priorities all users having 4 leaders

        # Test 5 users in Movement A (fully connected)
        _add_initial_followers(leader_id, mB_id)
        self.assertEqual(self.session.query(UserToUserLink).filter(
            UserToUserLink.leader_id == leader_id,
            UserToUserLink.follower_id.in_([u1_id, u2_id, u3_id, u4_id, u5_id]),
            UserToUserLink.movement_id == mB_id,
            UserToUserLink.destroyed.is_(None),
        ).count(), 0)  # This is 0 because we do not want to give any users more than 4 leaders

    def test_remove_all_followers(self):
        leader = self.create_user()
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
                UserToUserLink(mA, leader, None),

                # Movement B
                UserToUserLink(mB, u1, leader), UserToUserLink(mB, leader, u1),

                # Movement C
                UserToUserLink(mC, u1, leader), UserToUserLink(mC, u2, leader),
                UserToUserLink(mC, u1, None), UserToUserLink(mC, u2, None), UserToUserLink(mC, leader, None),
                
                # Movement D
                UserToUserLink(mD, u1, leader), UserToUserLink(mD, u2, leader), UserToUserLink(mD, u3, leader),
                UserToUserLink(mD, u1, u2), UserToUserLink(mD, u2, u3), UserToUserLink(mD, u3, u1),

                # Movement E
                UserToUserLink(mE, u1, u2), UserToUserLink(mE, u2, u3), UserToUserLink(mE, u3, u1),
                UserToUserLink(mE, u2, u1), UserToUserLink(mE, u3, u2), UserToUserLink(mE, u1, u3)
            ]
        )
        self.session.commit()
        leader_id = leader.id
        u1_id = u1.id
        u2_id = u2.id
        u3_id = u3.id
        mA_id = mA.id
        mB_id = mB.id
        mC_id = mC.id
        mD_id = mD.id
        mE_id = mE.id

        # Test removing all of 0 followers in movement A
        with freeze_time("2023-01-03 13:30:00+01:00"):
            _remove_all_followers(leader_id, mA_id)
        self.assertEqual(self.session.query(UserToUserLink).filter(
            UserToUserLink.leader_id == leader_id,
            UserToUserLink.movement_id == mA_id,
            UserToUserLink.destroyed == datetime(2023, 1, 3, 12, 30),
        ).count(), 0)
        self.assertEqual(self.session.query(UserToUserLink).filter(
            UserToUserLink.follower_id == leader_id,
            UserToUserLink.movement_id == mA_id,
            UserToUserLink.destroyed.is_(None),
        ).count(), 1)

        # Test removing all of 1 follower in movement B
        with freeze_time("2023-01-03 13:30:00+01:00"):
            _remove_all_followers(leader_id, mB_id)
        self.assertEqual(self.session.query(UserToUserLink).filter(
            UserToUserLink.leader_id == leader_id,
            UserToUserLink.movement_id == mB_id,
            UserToUserLink.destroyed == datetime(2023, 1, 3, 12, 30),
        ).count(), 1)

        # Test 2 users in movement C
        with freeze_time("2023-01-03 13:30:00+01:00"):
            _remove_all_followers(leader_id, mC_id)
        self.assertEqual(self.session.query(UserToUserLink).filter(
            UserToUserLink.leader_id == leader_id,
            UserToUserLink.movement_id == mC_id,
            UserToUserLink.destroyed == datetime(2023, 1, 3, 12, 30),
        ).count(), 2)
        self.assertEqual(self.session.query(UserToUserLink).filter(
            UserToUserLink.leader_id.in_([u1_id, u2_id]),
            UserToUserLink.follower_id.in_([u1_id, u2_id]),
            UserToUserLink.movement_id == mC_id,
            UserToUserLink.destroyed.is_(None),
        ).count(), 2)

        # Test 3 users in movement D
        with freeze_time("2023-01-03 13:30:00+01:00"):
            _remove_all_followers(leader_id, mD_id)
        self.assertEqual(self.session.query(UserToUserLink).filter(
            UserToUserLink.leader_id == leader_id,
            UserToUserLink.movement_id == mD_id,
            UserToUserLink.destroyed == datetime(2023, 1, 3, 12, 30),
        ).count(), 3)
        self.assertEqual(self.session.query(UserToUserLink).filter(
            UserToUserLink.leader_id == u3_id,
            UserToUserLink.follower_id == u1_id,
            UserToUserLink.movement_id == mD_id,
            UserToUserLink.destroyed.is_(None),
        ).count(), 1)

        # Test 3 users in movement E (follower not in movement)
        with freeze_time("2023-01-03 00:00:00+01:00"):
            _remove_all_followers(leader_id, mE_id)
        self.assertEqual(self.session.query(UserToUserLink).filter(
            UserToUserLink.movement_id == mE_id,
            UserToUserLink.destroyed.is_(None)
        ).count(), 6)


class TestPossibleLeaders(BaseTest):

    def test_possible_leaders(self):
        """
        movement1:
            1 -> 5   2   4
        movement2:
            1 -> 5   3
        """
        user1 = User("user1", "test1@test", "pass")
        user2 = User("user2", "test2@test", "pass")
        user3 = User("user3", "test3@test", "pass")
        user4 = User("user4", "test4@test", "pass")
        user5 = User("user5", "test5@test", "pass")

        movement1 = Movement("movement1", "twice daily")
        movement2 = Movement("movement2", "daily")

        assoc1 = UserToUserLink(movement1, user1, user2)
        assoc2 = UserToUserLink(movement1, user1, user4)
        assoc3 = UserToUserLink(movement1, user1, user5)
        assoc4 = UserToUserLink(movement1, user2, None)
        assoc5 = UserToUserLink(movement1, user3, None)
        assoc6 = UserToUserLink(movement1, user4, None)
        assoc7 = UserToUserLink(movement1, user5, None)
        assoc8 = UserToUserLink(movement2, user1, user3)
        assoc9 = UserToUserLink(movement2, user1, user5)
        assoc10 = UserToUserLink(movement2, user2, None)
        assoc11 = UserToUserLink(movement2, user3, None)
        assoc12 = UserToUserLink(movement2, user4, None)
        assoc13 = UserToUserLink(movement2, user5, None)

        self.session.add_all(
            [
                user1,
                user2,
                user3,
                user4,
                user5,
                movement1,
                movement2,
                assoc1,
                assoc2,
                assoc3,
                assoc4,
                assoc5,
                assoc6,
                assoc7,
                assoc8,
                assoc9,
                assoc10,
                assoc11,
                assoc12,
                assoc13,
            ]
        )
        self.session.commit()

        # Set because order does not matter
        self.assertEqual(
            set(possible_leaders(user1, movement1, self.session)), {user3}
        )
        self.assertEqual(
            set(possible_leaders(user1, movement2, self.session)),
            {user2, user4},
        )

        assoc1.destroy()

        self.assertEqual(
            set(possible_leaders(user1, movement1, self.session)),
            {user2, user3},
        )
        self.assertEqual(
            set(possible_leaders(user1, movement2, self.session)),
            {user2, user4},
        )


class LeaderControllersTest(BaseTest):
    def test_send_signal(self):
        user1 = self.create_user()
        movement1 = self.create_movement()
        user_to_user_link1 = UserToUserLink(movement1, user1, None)
        self.create_subscription(movement=movement1, user=user1)
        self.session.add_all([user1, movement1, user_to_user_link1])
        self.session.commit()

        send_signal(user1.id, movement1.id, "Test.")

        self.session.add_all([user1, movement1, user_to_user_link1])
        signal = self.session.query(Signal).first()
        self.assertEqual(signal.message, "Test.")
        self.assertEqual(signal.leader, user1)
        self.assertEqual(signal.movement, movement1)

    def test_send_signal_leader_not_in_movement(self):
        user1 = self.create_user()
        movement1 = self.create_movement()
        self.session.add_all([user1, movement1])
        self.session.commit()

        with self.assertRaises(AssertionError):
            send_signal(user1.id, movement1.id, "Test.")

    def test_send_signal_commit(self):
        user1 = self.create_user()
        movement1 = self.create_movement()
        assoc = UserToUserLink(movement1, user1)
        self.create_subscription(user=user1, movement=movement1)
        self.session.add(assoc)
        self.session.commit()
        send_signal(user1.id, movement1.id)

        self.session.add_all([user1, movement1])
        signal = self.session.query(Signal).get(1)
        self.assertIsNotNone(signal)
