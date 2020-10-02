from gridt.basetest import BaseTest
from gridt.models import User, MovementUserAssociation, Movement
from .helpers import leaders, possible_leaders, leaderless


class HelperIntegrationTest(BaseTest):
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

        assoc1 = MovementUserAssociation(movement, user1, user2)
        assoc2 = MovementUserAssociation(movement, user1, user3)
        assoc3 = MovementUserAssociation(movement, user2, user4)

        self.session.add_all([user1, user2, user3, assoc1, assoc2, assoc3])
        self.session.commit()

        self.assertEqual(
            len(list(leaders(user1, movement, self.session))), 2
        )
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

        assoc1 = MovementUserAssociation(movement, user1, user2)
        assoc2 = MovementUserAssociation(movement, user1, user3)
        assoc3 = MovementUserAssociation(movement, user1, user4)
        assoc3.destroy()

        self.session.add_all(
            [user1, user2, user3, user4, assoc1, assoc2, assoc3]
        )
        self.session.commit()

        self.assertEqual(
            len(list(leaders(user1, movement, self.session))), 2
        )
        self.assertEqual(
            set(leaders(movement, user1, self.session)),
            set([user2, user3]),
        )

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

        assoc1 = MovementUserAssociation(movement1, user1, user2)
        assoc2 = MovementUserAssociation(movement1, user1, user4)
        assoc3 = MovementUserAssociation(movement1, user1, user5)
        assoc4 = MovementUserAssociation(movement1, user2, None)
        assoc5 = MovementUserAssociation(movement1, user3, None)
        assoc6 = MovementUserAssociation(movement1, user4, None)
        assoc7 = MovementUserAssociation(movement1, user5, None)
        assoc8 = MovementUserAssociation(movement2, user1, user3)
        assoc9 = MovementUserAssociation(movement2, user1, user5)
        assoc10 = MovementUserAssociation(movement2, user2, None)
        assoc11 = MovementUserAssociation(movement2, user3, None)
        assoc12 = MovementUserAssociation(movement2, user4, None)
        assoc13 = MovementUserAssociation(movement2, user5, None)

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

    def test_leaderless(self):
        movement1 = Movement("test1", "daily")
        movement2 = Movement("test2", "daily")

        for i in range(6):
            user = User(f"user{i}", f"user{i}@email.com", "pass")
            self.session.add(user)
        users = self.session.query(User).all()

        MUA = MovementUserAssociation
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
            MUA(movement1, users[3], None),
            MUA(movement1, users[4], None),
            MUA(movement1, users[5], None),
            MUA(movement2, users[0], users[1]),
            MUA(movement2, users[0], users[2]),
            MUA(movement2, users[0], users[3]),
            MUA(movement2, users[1], None),
            MUA(movement2, users[2], None),
            MUA(movement2, users[3], None),
        ]
        self.session.add_all(muas)
        self.session.commit()

        self.assertEqual(
            set(leaderless(users[0], movement1, self.session)),
            set(users[3:]),
        )
        self.assertEqual(
            set(leaderless(users[0], movement2, self.session)), set(users[1:4])
        )

        mua1 = self.session.query(MUA).filter(MUA.id == 1).one()
        mua1.destroy()

        self.assertEqual(
            set(leaderless(users[0], movement1, self.session)),
            set(users[3:]),
        )
        self.assertEqual(
            set(leaderless(users[0], movement2, self.session)), set(users[1:4])
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
            set(leaderless(users[0], movement1, self.session)),
            set([users[3], users[4], users[5]]),
        )
        self.assertEqual(
            set(leaderless(users[0], movement2, self.session)),
            set(users[1:4]),
        )
