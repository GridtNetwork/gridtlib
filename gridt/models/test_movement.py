from gridt.basetest import BaseTest
from . import MovementUserAssociation, Movement


class UnitTestMovement(BaseTest):
    def test_create(self):
        movement1 = Movement("movement1", "daily")

        self.assertEqual(movement1.name, "movement1")
        self.assertEqual(movement1.interval, "daily")
        self.assertEqual(movement1.short_description, "")
        self.assertEqual(movement1.description, "")

        movement2 = Movement(
            "toothpicking", "twice daily", "pick your teeth every day!"
        )

        self.assertEqual(movement2.name, "toothpicking")
        self.assertEqual(movement2.interval, "twice daily")
        self.assertEqual(
            movement2.short_description, "pick your teeth every day!"
        )
        self.assertEqual(movement2.description, "")


class IntegrationTestUser(BaseTest):
    def test_active_users(self):
        user1 = self.create_user()
        user2 = self.create_user()
        user3 = self.create_user()
        user4 = self.create_user()
        movement1 = self.create_movement()
        movement2 = self.create_movement()
        assoc1 = MovementUserAssociation(movement1, user1, user3)

        # Destroyed associations should not result in active users.
        assoc2 = MovementUserAssociation(movement1, user2, user3)
        assoc2.destroy()

        # Leaders should only show up once.
        assoc3 = MovementUserAssociation(movement2, user2, None)
        assoc4 = MovementUserAssociation(movement1, user3, user1)

        # Having an empty leader should not change if it's state.
        assoc5 = MovementUserAssociation(movement1, user3, None)

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
            ]
        )
        self.session.commit()

        self.assertEqual(set(movement1.active_users), set((user1, user3)))
        self.assertEqual(movement1.active_users.count(), 2)
