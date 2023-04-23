"""Test for leader controller."""
from gridt.tests.basetest import BaseTest
from gridt.models import UserToUserLink, Signal, User, Movement
from gridt.models import Subscription as SUB
from gridt.controllers.leader import (
    send_signal,
    add_initial_followers,
    remove_all_followers,
    possible_leaders,
    get_last_signal
)
from freezegun import freeze_time
from datetime import datetime


class OnSubscriptionEventsLeaderTests(BaseTest):
    """Test the functions dependent on subscriptions."""

    def test_add_initial_followers(self):
        """Unittest for add_initial_followers."""
        leader = self.create_user()
        u1 = self.create_user()
        u2 = self.create_user()
        u3 = self.create_user()
        u4 = self.create_user()
        u5 = self.create_user()
        mA = self.create_movement()
        mB = self.create_movement()
        self.session.add_all([
            # Movement A
            UserToUserLink(mA, u1, u2),
            UserToUserLink(mA, u1, u3), UserToUserLink(mA, u2, u3),
            UserToUserLink(mA, u2, u4), UserToUserLink(mA, u3, u4),
            UserToUserLink(mA, u3, u5), UserToUserLink(mA, u4, u5),
            UserToUserLink(mA, u3, u1), UserToUserLink(mA, u5, u1),
            UserToUserLink(mA, u5, u2),
            SUB(u1, mA), SUB(u2, mA),
            SUB(u3, mA), SUB(u4, mA),
            SUB(u5, mA),

            # Movement B
            UserToUserLink(mB, u1, u2), UserToUserLink(mB, u1, u3),
            UserToUserLink(mB, u1, u4), UserToUserLink(mB, u1, u5),
            UserToUserLink(mB, u2, u3), UserToUserLink(mB, u2, u4),
            UserToUserLink(mB, u2, u5), UserToUserLink(mB, u2, u1),
            UserToUserLink(mB, u3, u4), UserToUserLink(mB, u3, u5),
            UserToUserLink(mB, u3, u1), UserToUserLink(mB, u3, u2),
            UserToUserLink(mB, u4, u5), UserToUserLink(mB, u4, u1),
            UserToUserLink(mB, u4, u2), UserToUserLink(mB, u4, u3),
            UserToUserLink(mB, u5, u1), UserToUserLink(mB, u5, u2),
            UserToUserLink(mB, u5, u3), UserToUserLink(mB, u5, u4),
            SUB(u1, mB), SUB(u2, mB), SUB(u3, mB), SUB(u4, mB), SUB(u5, mB)
        ])
        self.session.commit()
        leader_id = leader.id
        u1_id = u1.id
        u2_id = u2.id
        u3_id = u3.id
        u4_id = u4.id
        u5_id = u5.id
        mA_id = mA.id
        mB_id = mB.id
        user_ids = [u1_id, u2_id, u3_id, u4_id, u5_id]

        # Test 5 users in Movement A (partily connected)
        add_initial_followers(leader_id, mA_id)
        self.assertEqual(self.session.query(UserToUserLink).filter(
            UserToUserLink.leader_id == leader_id,
            UserToUserLink.follower_id.in_(user_ids),
            UserToUserLink.movement_id == mA_id,
            UserToUserLink.destroyed.is_(None),
        ).count(), 5, "Prioritize all users having 4 leaders")

        # Test 5 users in Movement A (fully connected)
        add_initial_followers(leader_id, mB_id)
        self.assertEqual(self.session.query(UserToUserLink).filter(
            UserToUserLink.leader_id == leader_id,
            UserToUserLink.follower_id.in_(user_ids),
            UserToUserLink.movement_id == mB_id,
            UserToUserLink.destroyed.is_(None),
        ).count(), 0, "Don't give any users more than 4 leaders")

    def test_remove_all_followers(self):
        """Tests for removing all_followers."""
        leader = self.create_user()
        u1 = self.create_user()
        u2 = self.create_user()
        u3 = self.create_user()
        mA = self.create_movement()
        mB = self.create_movement()
        mC = self.create_movement()
        mD = self.create_movement()
        mE = self.create_movement()
        self.session.add_all([
            # Movement A
            SUB(leader, mA),

            # Movement B
            UserToUserLink(mB, u1, leader), UserToUserLink(mB, leader, u1),
            SUB(u1, mB), SUB(leader, mB),

            # Movement C
            UserToUserLink(mC, u1, leader), UserToUserLink(mC, u2, leader),
            SUB(u1, mC), SUB(leader, mC), SUB(u2, mC),

            # Movement D
            UserToUserLink(mD, u1, leader), UserToUserLink(mD, u2, leader),
            UserToUserLink(mD, u3, leader), UserToUserLink(mD, u1, u2),
            UserToUserLink(mD, u2, u3), UserToUserLink(mD, u3, u1),
            SUB(u1, mD), SUB(leader, mD), SUB(u2, mD), SUB(u3, mD),

            # Movement E
            UserToUserLink(mE, u1, u2), UserToUserLink(mE, u2, u3),
            UserToUserLink(mE, u3, u1), UserToUserLink(mE, u2, u1),
            UserToUserLink(mE, u3, u2), UserToUserLink(mE, u1, u3),
            SUB(u1, mE), SUB(u3, mE), SUB(u2, mE)
        ])
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
            remove_all_followers(leader_id, mA_id)
        self.assertEqual(self.session.query(UserToUserLink).filter(
            UserToUserLink.leader_id == leader_id,
            UserToUserLink.movement_id == mA_id,
            UserToUserLink.destroyed == datetime(2023, 1, 3, 12, 30),
        ).count(), 0)

        # Test removing all of 1 follower in movement B
        with freeze_time("2023-01-03 13:30:00+01:00"):
            remove_all_followers(leader_id, mB_id)
        self.assertEqual(self.session.query(UserToUserLink).filter(
            UserToUserLink.leader_id == leader_id,
            UserToUserLink.movement_id == mB_id,
            UserToUserLink.destroyed == datetime(2023, 1, 3, 12, 30),
        ).count(), 1)

        # Test 2 users in movement C
        with freeze_time("2023-01-03 13:30:00+01:00"):
            remove_all_followers(leader_id, mC_id)
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
            remove_all_followers(leader_id, mD_id)
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
            remove_all_followers(leader_id, mE_id)
        self.assertEqual(self.session.query(UserToUserLink).filter(
            UserToUserLink.movement_id == mE_id,
            UserToUserLink.destroyed.is_(None)
        ).count(), 6)


class TestPossibleLeaders(BaseTest):
    """Tests to get the possible leaders."""

    def test_possible_leaders(self):
        """
        Unittest for possible_leaders.

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
        assoc8 = UserToUserLink(movement2, user1, user3)
        assoc9 = UserToUserLink(movement2, user1, user5)
        sub1 = SUB(user1, movement1)
        sub2 = SUB(user2, movement1)
        sub3 = SUB(user3, movement1)
        sub4 = SUB(user4, movement1)
        sub5 = SUB(user5, movement1)

        sub6 = SUB(user1, movement2)
        sub7 = SUB(user2, movement2)
        sub8 = SUB(user3, movement2)
        sub9 = SUB(user4, movement2)
        sub10 = SUB(user5, movement2)

        self.session.add_all([
            user1, user2, user3, user4, user5,
            movement1, movement2,
            assoc1, assoc2, assoc3,
            sub1, sub2, sub3, sub4, sub5, sub6, sub7, sub8, sub9, sub10,
            assoc8, assoc9,
        ])
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
    """Unittest for leader signals."""

    def test_send_signal(self):
        """Unittest for send_signal."""
        user1 = self.create_user()
        movement1 = self.create_movement()
        self.create_subscription(movement=movement1, user=user1)
        self.session.add_all([user1, movement1])
        self.session.commit()

        send_signal(user1.id, movement1.id, "Test.")

        self.session.add_all([user1, movement1])
        signal = self.session.query(Signal).first()
        self.assertEqual(signal.message, "Test.")
        self.assertEqual(signal.leader, user1)
        self.assertEqual(signal.movement, movement1)

    def test_send_signal_leader_not_in_movement(self):
        """Unittest for send_signal case not in a movement."""
        user1 = self.create_user()
        movement1 = self.create_movement()
        self.session.add_all([user1, movement1])
        self.session.commit()

        with self.assertRaises(AssertionError):
            send_signal(user1.id, movement1.id, "Test.")

    def test_send_signal_commit(self):
        """Unittest for sending a signal without message."""
        user1 = self.create_user()
        movement1 = self.create_movement()
        self.create_subscription(user=user1, movement=movement1)
        self.session.commit()
        send_signal(user1.id, movement1.id)

        self.session.add_all([user1, movement1])
        signal = self.session.get(Signal, 1)
        self.assertIsNotNone(signal)


class FindSignalTest(BaseTest):
    """Tests for getting signals."""

    def test_find_signal(self):
        """Unittest for get_last_signal."""
        user1 = self.create_user()
        user2 = self.create_user()
        movement1 = self.create_movement()
        movement2 = self.create_movement()
        self.create_subscription(movement=movement1, user=user1)
        self.create_subscription(movement=movement1, user=user2)
        self.create_subscription(movement=movement2, user=user1)
        self.create_subscription(movement=movement2, user=user2)

        self.session.add_all([user1, user2, movement1, movement2])
        self.session.commit()
        u1_id = user1.id
        u2_id = user2.id
        m1_id = movement1.id
        m2_id = movement2.id

        dates = [datetime(1996, 3, day) for day in range(15, 30)]
        with freeze_time(dates[0]):
            send_signal(u1_id, m1_id)
        with freeze_time(dates[1]):
            send_signal(u1_id, m2_id)
        with freeze_time(dates[2]):
            send_signal(u1_id, m1_id)
        with freeze_time(dates[3]):
            send_signal(u2_id, m2_id)
        with freeze_time(dates[4]):
            send_signal(u2_id, m1_id)
        with freeze_time(dates[5]):
            send_signal(u2_id, m1_id)

        self.session.add_all([user1, movement1])
        signal = get_last_signal(u1_id, m1_id, self.session)
        self.assertEqual(signal.time_stamp, dates[2])
