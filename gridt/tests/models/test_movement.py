"""Tests for Movement Model."""
from gridt.tests.basetest import BaseTest
from gridt.models import Movement


class UnitTestMovement(BaseTest):
    """Movement Model unittests."""

    def test_create(self):
        """Unittest for __init__."""
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
        """Unittest for to_json."""
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
