"""Test for follower controller."""
from freezegun import freeze_time
from unittest.mock import patch
from gridt.tests.basetest import BaseTest
from gridt.models import User, Movement, UserToUserLink
from gridt.models import Subscription as SUB
from gridt.models import Signal
from gridt.controllers.follower import (
    swap_leader,
    get_leader,
    add_initial_leaders,
    remove_all_leaders,
    possible_followers,
    get_leaders
)
from gridt.controllers.leader import send_signal
from datetime import datetime


class TestLeaderlessFollowers(BaseTest):
    """Test for adding a follower to a movement."""

    def test_possible_followers(self):
        """Test for possible_followers."""
        movement1 = Movement("test1", "daily")
        movement2 = Movement("test2", "daily")

        for i in range(6):
            user = User(f"user{i}", f"user{i}@email.com", "pass")
            self.session.add(user)
        users = self.session.query(User).all()

        user_to_user_links = [
            UserToUserLink(movement1, users[0], users[1]),
            UserToUserLink(movement1, users[0], users[2]),
            UserToUserLink(movement1, users[0], users[3]),
            UserToUserLink(movement1, users[1], users[0]),
            UserToUserLink(movement1, users[1], users[2]),
            UserToUserLink(movement1, users[1], users[3]),
            UserToUserLink(movement1, users[2], users[1]),
            UserToUserLink(movement1, users[2], users[5]),
            UserToUserLink(movement1, users[2], users[3]),
            UserToUserLink(movement1, users[2], users[4]),
            UserToUserLink(movement2, users[0], users[1]),
            UserToUserLink(movement2, users[0], users[2]),
            UserToUserLink(movement2, users[0], users[3]),
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

        self.session.add_all(user_to_user_links)
        self.session.commit()

        self.assertEqual(
            set(possible_followers(users[0], movement2, self.session)),
            set(users[1:4]),
        )

        self.assertEqual(
            set(possible_followers(users[0], movement1, self.session)),
            set(users[3:]),
        )

        user_to_user_link1 = self.session.query(UserToUserLink).filter(
            UserToUserLink.id == 1
        ).one()
        user_to_user_link1.destroy()

        self.assertEqual(
            set(possible_followers(users[0], movement1, self.session)),
            set(users[3:]),
        )
        self.assertEqual(
            set(possible_followers(users[0], movement2, self.session)),
            set(users[1:4]),
        )

        user_to_user_link2 = (
            self.session.query(UserToUserLink)
            .filter(
                UserToUserLink.follower_id == users[1].id,
                UserToUserLink.leader_id == users[2].id,
                UserToUserLink.movement_id == movement1.id,
            )
            .one()
        )
        user_to_user_link2.destroy()

        self.assertEqual(
            set(possible_followers(users[0], movement1, self.session)),
            set([users[3], users[4], users[5]]),
        )
        self.assertEqual(
            set(possible_followers(users[0], movement2, self.session)),
            set(users[1:4]),
        )


class OnSubscriptionEventsFollowerTests(BaseTest):
    """Test the functions dependent on subscriptions."""

    def test_add_initial_leaders(self):
        """Unittest for add_initial_leaders."""
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
        self.session.add_all([
            # Movement B
            SUB(u1, mB),

            # Movement C
            UserToUserLink(mC, u1, u2), UserToUserLink(mC, u2, u1),
            SUB(u1, mC),
            SUB(u2, mC),

            # Movement D
            UserToUserLink(mD, u1, u2), UserToUserLink(mD, u1, u3),
            UserToUserLink(mD, u2, u3), UserToUserLink(mD, u2, u4),
            UserToUserLink(mD, u3, u4), UserToUserLink(mD, u3, u5),
            UserToUserLink(mD, u4, u5), UserToUserLink(mD, u3, u1),
            UserToUserLink(mD, u5, u1), UserToUserLink(mD, u5, u2),
            SUB(u1, mD), SUB(u2, mD), SUB(u3, mD), SUB(u4, mD),
            SUB(u5, mD),

            # Movement E
            UserToUserLink(mE, u1, u2), UserToUserLink(mE, u1, u3),
            UserToUserLink(mE, u1, u4), UserToUserLink(mE, u1, u5),
            UserToUserLink(mE, u2, u3), UserToUserLink(mE, u2, u4),
            UserToUserLink(mE, u2, u5), UserToUserLink(mE, u2, u1),
            UserToUserLink(mE, u3, u4), UserToUserLink(mE, u3, u5),
            UserToUserLink(mE, u3, u1), UserToUserLink(mE, u3, u2),
            UserToUserLink(mE, u4, u5), UserToUserLink(mE, u4, u1),
            UserToUserLink(mE, u4, u2), UserToUserLink(mE, u4, u3),
            UserToUserLink(mE, u5, u1), UserToUserLink(mE, u5, u2),
            UserToUserLink(mE, u5, u3), UserToUserLink(mE, u5, u4),
            SUB(u1, mE), SUB(u2, mE), SUB(u3, mE), SUB(u4, mE), SUB(u5, mE)
        ])
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
        self.assertEqual(self.session.query(UserToUserLink).filter(
            UserToUserLink.movement_id == mA_id
        ).count(), 0)

        # Test 1 user in movement B
        add_initial_leaders(follower_id, mB_id)
        self.assertEqual(self.session.query(UserToUserLink).filter(
            UserToUserLink.movement_id == mB_id,
            UserToUserLink.follower_id == follower_id
        ).count(), 1)
        self.assertEqual(self.session.query(UserToUserLink).filter(
            UserToUserLink.follower_id == follower_id,
            UserToUserLink.movement_id == mB_id,
            UserToUserLink.leader_id == u1_id,
            UserToUserLink.destroyed.is_(None),
        ).count(), 1)

        # Test 2 users in movement C
        add_initial_leaders(follower_id, mC_id)
        self.assertEqual(self.session.query(UserToUserLink).filter(
            UserToUserLink.follower_id == follower_id,
            UserToUserLink.movement_id == mC_id,
            UserToUserLink.destroyed.is_(None),
        ).count(), 2)
        self.assertEqual(self.session.query(UserToUserLink).filter(
            UserToUserLink.follower_id == follower_id,
            UserToUserLink.leader_id == u1_id,
            UserToUserLink.movement_id == mC_id,
            UserToUserLink.destroyed.is_(None),
        ).count(), 1)
        self.assertEqual(self.session.query(UserToUserLink).filter(
            UserToUserLink.follower_id == follower_id,
            UserToUserLink.leader_id == u2_id,
            UserToUserLink.movement_id == mC_id,
            UserToUserLink.destroyed.is_(None),
        ).count(), 1)

        # Test 5 users in movement D
        add_initial_leaders(follower_id, mD_id)
        self.assertEqual(self.session.query(UserToUserLink).filter(
            UserToUserLink.follower_id == follower_id,
            UserToUserLink.leader_id.in_([u1_id, u2_id, u3_id, u4_id, u5_id]),
            UserToUserLink.movement_id == mD_id,
            UserToUserLink.destroyed.is_(None),
        ).count(), 4)

        # Test 5 users in movement E but all leaders have 4 followers
        add_initial_leaders(follower_id, mE_id)
        self.assertEqual(self.session.query(UserToUserLink).filter(
            UserToUserLink.follower_id == follower_id,
            UserToUserLink.leader_id.in_([u1_id, u2_id, u3_id, u4_id, u5_id]),
            UserToUserLink.movement_id == mE_id,
            UserToUserLink.destroyed.is_(None),
        ).count(), 4)

    def test_remove_all_leaders(self):
        """Unittest for remove_all_leaders."""
        follower = self.create_user()
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
            SUB(follower, mA),

            # Movement B
            UserToUserLink(mB, follower, u1),
            SUB(follower, mB), SUB(u1, mB),

            # Movement C
            UserToUserLink(mC, follower, u1), UserToUserLink(mC, follower, u2),
            SUB(follower, mC), SUB(u1, mC), SUB(u2, mC),

            # Movement D
            UserToUserLink(mD, follower, u1), UserToUserLink(mD, follower, u2),
            UserToUserLink(mD, follower, u3), UserToUserLink(mD, u1, u2),
            UserToUserLink(mD, u2, u3), UserToUserLink(mD, u3, u1),
            SUB(follower, mD), SUB(u1, mD), SUB(u2, mD), SUB(u3, mD),

            # Movement E
            UserToUserLink(mE, u1, u2), UserToUserLink(mE, u2, u3),
            UserToUserLink(mE, u3, u1), UserToUserLink(mE, u2, u1),
            UserToUserLink(mE, u3, u2), UserToUserLink(mE, u1, u3),
            SUB(u1, mE), SUB(u2, mE), SUB(u3, mE)
        ])

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
        self.assertEqual(self.session.query(UserToUserLink).filter(
            UserToUserLink.follower_id == follower_id,
            UserToUserLink.movement_id == mA_id,
            UserToUserLink.destroyed == datetime(2023, 1, 2, 23, 0),
        ).count(), 0)

        # Test 1 user in movement B
        with freeze_time("2023-01-03 00:00:00+01:00"):
            remove_all_leaders(follower_id, mB_id)
        self.assertEqual(self.session.query(UserToUserLink).filter(
            UserToUserLink.follower_id == follower_id,
            UserToUserLink.leader_id == u1_id,
            UserToUserLink.movement_id == mB_id,
            UserToUserLink.destroyed == datetime(2023, 1, 2, 23, 0),
        ).count(), 1)
        self.assertEqual(self.session.query(UserToUserLink).filter(
            UserToUserLink.movement_id == mB_id,
            UserToUserLink.destroyed.is_(None)
        ).count(), 0)

        # Test 2 users in movement C
        with freeze_time("2023-01-03 00:00:00+01:00"):
            remove_all_leaders(follower_id, mC_id)
        self.assertEqual(self.session.query(UserToUserLink).filter(
            UserToUserLink.follower_id == follower_id,
            UserToUserLink.movement_id == mC_id,
            UserToUserLink.destroyed == datetime(2023, 1, 2, 23, 0)
        ).count(), 2)
        self.assertEqual(self.session.query(UserToUserLink).filter(
            UserToUserLink.movement_id == mC_id,
            UserToUserLink.destroyed.is_(None)
        ).count(), 2)

        # Test 3 users in movement D
        with freeze_time("2023-01-03 00:00:00+01:00"):
            remove_all_leaders(follower_id, mD_id)
        self.assertEqual(self.session.query(UserToUserLink).filter(
            UserToUserLink.follower_id == follower_id,
            UserToUserLink.movement_id == mD_id,
            UserToUserLink.destroyed == datetime(2023, 1, 2, 23, 0)
        ).count(), 3)
        self.assertEqual(self.session.query(UserToUserLink).filter(
            UserToUserLink.follower_id == u1_id,
            UserToUserLink.movement_id == mD_id,
            UserToUserLink.destroyed.is_(None)
        ).count(), 2)
        self.assertEqual(self.session.query(UserToUserLink).filter(
            UserToUserLink.follower_id == u2_id,
            UserToUserLink.movement_id == mD_id,
            UserToUserLink.destroyed.is_(None)
        ).count(), 2)
        self.assertEqual(self.session.query(UserToUserLink).filter(
            UserToUserLink.follower_id == u3_id,
            UserToUserLink.movement_id == mD_id,
            UserToUserLink.destroyed.is_(None)
        ).count(), 2)

        # Test 3 users in movement E (follower not in movement)
        with freeze_time("2023-01-03 00:00:00+01:00"):
            remove_all_leaders(follower_id, mE_id)
        self.assertEqual(self.session.query(UserToUserLink).filter(
            UserToUserLink.movement_id == mE_id,
            UserToUserLink.destroyed.is_(None)
        ).count(), 6)


class GetLeaderTest(BaseTest):
    """Unittest for get_leader function."""

    @patch(
        "gridt.controllers.follower.User.get_email_hash",
        return_value="email_hash",
    )
    def test_get_leader(self, avatar_func):
        """
        Test for get_leader.

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
                UserToUserLink(movement1, follower, leader1),
                UserToUserLink(movement1, follower, leader2),
                UserToUserLink(movement2, follower, leader1),
                UserToUserLink(movement2, leader2, follower),
            ]
        )
        self.session.commit()

        l1_id = leader1.id
        l1_name = leader1.username
        l2_id = leader2.id
        f_id = follower.id
        m1_id = movement1.id
        m2_id = movement2.id

        earlier = datetime(1995, 1, 15, 12)
        later = datetime(1996, 3, 15, 12)
        with freeze_time(earlier):
            send_signal(l1_id, m1_id, "Message1")
            send_signal(l1_id, m2_id, "Message2")
            send_signal(l2_id, m1_id, "Message3")
        with freeze_time(later):
            send_signal(l1_id, m1_id, "Message4")

        self.assertDictEqual(
            get_leader(f_id, m1_id, l1_id),
            {
                "id": l1_id,
                "bio": "",
                "avatar": "email_hash",
                "username": l1_name,
                "is_admin": False,
                "message_history": [
                    {
                        "message": "Message4",
                        "time_stamp": str(later.astimezone()),
                    },
                    {
                        "message": "Message1",
                        "time_stamp": str(earlier.astimezone()),
                    },
                ],
            },
        )


class SwapTest(BaseTest):
    """Test for swap leaders."""

    def test_swap(self):
        """
        Unittest for swap leaders.

        movement1:
            1 <-> 2 4 5
        """
        user1 = User("user1", "test1@test.com", "password")
        user2 = User("user2", "test2@test.com", "password")
        user3 = User("user3", "test3@test.com", "password")
        movement = Movement("movement1", "daily")

        self.session.add_all([user1, user2, user3, movement])
        self.session.commit()

        assoc1 = UserToUserLink(movement, user1, user2)
        assoc2 = UserToUserLink(movement, user2, user1)
        self.session.commit()

        self.assertFalse(swap_leader(user1.id, movement.id, user2.id))
        self.session.add_all([user1, user2, user3, movement])

        user4 = User("user4", "test4@test.com", "password")
        user5 = User("user5", "test5@test.com", "password")
        sub3 = SUB(user4, movement)
        sub4 = SUB(user5, movement)
        self.session.add_all([user1, user2, user3, movement])
        self.session.add_all([user4, user5, assoc1, assoc2, sub3, sub4])
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
        self.session.add_all([user4, user5, assoc1, assoc2, sub3, sub4])
        self.assertEqual(len(get_leaders(user2, movement, self.session)), 1)

    def test_swap_last_signal(self):
        movement_1 = Movement("movement1", "daily")
        user_1 = User("user1", "test1@test.com", "password")
        subscription_1 = SUB(user_1, movement_1)
        user_2 = User("user2", "test2@test.com", "password")
        subscription_2 = SUB(user_2, movement_1)
        user_3 = User("user3", "test3@test.com", "password")
        subscription_3 = SUB(user_3, movement_1)
        user_4 = User("user4", "test4@test.com", "password")
        subscription_4 = SUB(user_4, movement_1)
        user_5 = User("user5", "test5@test.com", "password")
        subscription_5 = SUB(user_5, movement_1)
        signaller = User('signaller', 'signal@test.com', 'password')
        subscription_6 = SUB(signaller, movement_1)
        link_1_to_2 = UserToUserLink(movement_1, user_1, user_2)
        link_1_to_3 = UserToUserLink(movement_1, user_1, user_3)
        link_1_to_4 = UserToUserLink(movement_1, user_1, user_4)
        link_1_to_5 = UserToUserLink(movement_1, user_1, user_5)

        signal_time = datetime(2023, 9, 2, 14)
        with freeze_time(signal_time):
            message = 'Hello World'
            signal = Signal(signaller, movement_1, message)

        self.session.add_all([
            movement_1, user_1, user_2, user_3, user_4, user_5, signaller,
            subscription_1, subscription_2, subscription_3, subscription_4, subscription_5, subscription_6,
            link_1_to_2, link_1_to_3, link_1_to_4, link_1_to_5,
            signal
        ])
        self.session.commit()

        new_leader = swap_leader(user_1.id, movement_1.id, user_2.id)
        self.assertEqual(new_leader['last_signal']['message'], message)
        self.assertEqual(new_leader['last_signal']['time_stamp'], str(signal_time.astimezone()))

    def test_swap_last_signal_no_message(self):
        movement_1 = Movement("movement1", "daily")
        user_1 = User("user1", "test1@test.com", "password")
        subscription_1 = SUB(user_1, movement_1)
        user_2 = User("user2", "test2@test.com", "password")
        subscription_2 = SUB(user_2, movement_1)
        user_3 = User("user3", "test3@test.com", "password")
        subscription_3 = SUB(user_3, movement_1)
        user_4 = User("user4", "test4@test.com", "password")
        subscription_4 = SUB(user_4, movement_1)
        user_5 = User("user5", "test5@test.com", "password")
        subscription_5 = SUB(user_5, movement_1)
        signaller = User('signaller', 'signal@test.com', 'password')
        subscription_6 = SUB(signaller, movement_1)
        link_1_to_2 = UserToUserLink(movement_1, user_1, user_2)
        link_1_to_3 = UserToUserLink(movement_1, user_1, user_3)
        link_1_to_4 = UserToUserLink(movement_1, user_1, user_4)
        link_1_to_5 = UserToUserLink(movement_1, user_1, user_5)

        earlier = datetime(2023, 9, 2, 14)
        later = datetime(2023, 9, 2, 15)
        with freeze_time(earlier):
            message = 'Hello World'
            signal_1 = Signal(signaller, movement_1, message)

        with freeze_time(later):
            signal_2 = Signal(signaller, movement_1)

        self.session.add_all([
            movement_1, user_1, user_2, user_3, user_4, user_5, signaller,
            subscription_1, subscription_2, subscription_3, subscription_4, subscription_5, subscription_6,
            link_1_to_2, link_1_to_3, link_1_to_4, link_1_to_5,
            signal_1, signal_2
        ])
        self.session.commit()

        new_leader = swap_leader(user_1.id, movement_1.id, user_2.id)
        self.assertIsNone(new_leader['last_signal']['message'])
        self.assertEqual(new_leader['last_signal']['time_stamp'], str(later.astimezone()))


    def test_swap_leader_complicated(self):
        """
        Unittest for swap_leader.

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

        assoc1 = UserToUserLink(movement1, user1, user2)
        assoc2 = UserToUserLink(movement1, user2, user1)
        assoc3 = UserToUserLink(movement1, user3, user1)
        assoc4 = UserToUserLink(movement1, user1, user4)
        assoc5 = UserToUserLink(movement2, user1, user5)
        assoc6 = UserToUserLink(movement2, user5, user1)
        sub1 = SUB(user1, movement1)
        sub2 = SUB(user2, movement1)
        sub3 = SUB(user3, movement1)
        sub4 = SUB(user4, movement1)
        sub5 = SUB(user1, movement2)
        sub6 = SUB(user5, movement2)

        self.session.add_all([
            user1, user2, user3, user4,
            movement1, movement2,
            assoc1, assoc2, assoc3, assoc4, assoc5, assoc6,
            sub1, sub2, sub3, sub4, sub5, sub6
        ])
        self.session.commit()

        new_leader = swap_leader(user1.id, movement1.id, user2.id)
        # Make sure that it is actually saved in the database!
        self.session.rollback()
        self.session.add(user3)
        self.assertEqual(new_leader, user3.to_json())

        self.session.add_all([user1, movement2, user5])
        self.assertIsNone(swap_leader(user1.id, movement2.id, user5.id))


class TestGetLeaders(BaseTest):
    """Test get_leaders."""

    def test_get_leaders(self):
        """
        Unittest for get_leaders.

        movement1:
            3 <- 1 -> 2 -> 4
        """
        user1 = User("user1", "test1@test.com", "test")
        user2 = User("user2", "test2@test.com", "test")
        user3 = User("user3", "test3@test.com", "test")
        user4 = User("user4", "test4@test.com", "test")

        movement = Movement("movement1", "daily")

        assoc1 = UserToUserLink(movement, user1, user2)
        assoc2 = UserToUserLink(movement, user1, user3)
        assoc3 = UserToUserLink(movement, user2, user4)

        self.session.add_all([user1, user2, user3, assoc1, assoc2, assoc3])
        self.session.commit()

        self.assertEqual(len(get_leaders(user1, movement, self.session)), 2)
        self.assertEqual(
            set(get_leaders(user1, movement, self.session)),
            set([user2, user3]),
        )

    def test_get_leaders_removed(self):
        """
        Unittest for get_leaders in case of removal.

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

        assoc1 = UserToUserLink(movement, user1, user2)
        assoc2 = UserToUserLink(movement, user1, user3)
        assoc3 = UserToUserLink(movement, user1, user4)
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
