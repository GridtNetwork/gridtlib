from gridt.tests.basetest import BaseTest
from gridt.models import MovementToMovementLink, Movement


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

    def test_to_json(self):
        movement = Movement(
            "movement1",
            "daily",
            short_description="Hi",
            description="A long description",
        )
        self.session.add(movement)
        self.session.commit()
        expected = {
            "id": 1,
            "name": "movement1",
            "short_description": "Hi",
            "description": "A long description",
            "interval": "daily",
        }
        self.assertEqual(movement.to_json(), expected)

