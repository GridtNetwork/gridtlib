from datetime import datetime
from freezegun import freeze_time
from gridt.tests.basetest import BaseTest
from gridt.models import User, MovementUserAssociation as MUA, Movement
from gridt.controllers.helpers import (
    leaders,
    _find_last_signal,
)
from gridt.controllers.leader import send_signal

class TestHelpers(BaseTest):
    def test_leaders(self):
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

        self.assertEqual(len(leaders(user1, movement, self.session)), 2)
        self.assertEqual(
            set(leaders(user1, movement, self.session)),
            set([user2, user3]),
        )

    def test_leaders_removed(self):
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

        self.assertEqual(len(leaders(user1, movement, self.session)), 2)
        self.assertEqual(
            set(leaders(movement, user1, self.session)),
            set([user2, user3]),
        )


class FindSignalTest(BaseTest):
    def test_find_signal(self):
        user1 = self.create_user()
        user2 = self.create_user()
        movement1 = self.create_movement()
        movement2 = self.create_movement()
        self.create_subscription(movement=movement1, user=user1)
        self.create_subscription(movement=movement1, user=user2)
        self.create_subscription(movement=movement2, user=user1)
        self.create_subscription(movement=movement2, user=user2)
        assoc1 = MUA(movement1, user1)
        assoc2 = MUA(movement1, user2)
        assoc3 = MUA(movement2, user1)
        assoc4 = MUA(movement2, user2)
        self.session.add_all(
            [
                user1,
                user2,
                movement1,
                movement2,
                assoc1,
                assoc2,
                assoc3,
                assoc4,
            ]
        )
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
        signal = _find_last_signal(u1_id, m1_id, self.session)
        self.assertEqual(signal.time_stamp, dates[2])
