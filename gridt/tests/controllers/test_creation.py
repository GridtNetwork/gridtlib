"""Test for creation controller."""
from ..basetest import BaseTest

from gridt.controllers.creation import (
    _get_creation,
    is_creator,
    new_movement_by_user,
    remove_creation
)
import gridt.exc as E
from gridt.models.creation import Creation


class CreationControllerTest(BaseTest):
    """Unittest for creation controller."""

    def test_helper_get_creation(self):
        """Unittest for _get_creation."""
        user = self.create_user()
        movement = self.create_movement()

        self.session.commit()

        user_id = user.id
        movement_id = movement.id

        with self.assertRaises(E.UserIsNotCreator):
            _get_creation(user_id, movement_id, self.session)

        creation1 = Creation(user, movement)
        self.session.add(creation1)

        creation2 = _get_creation(user_id, movement_id, self.session)
        self.assertEqual(creation1.id, creation2.id)
        self.assertEqual(creation1.user_id, creation2.user_id)
        self.assertEqual(creation1.movement_id, creation2.movement_id)

    def test_is_creator(self):
        """Unittest for is_creator."""
        u1 = self.create_user()
        u2 = self.create_user()
        u3 = self.create_user()

        m1 = self.create_movement()
        m2 = self.create_movement()

        user_1_id, user_2_id, user_3_id = u1.id, u2.id, u3.id
        movement_1_id, movement_2_id = m1.id, m2.id

        creation_relation_1 = Creation(u2, m1)
        creation_relation_2 = Creation(u3, m2)
        creation_relation_2.end()

        self.session.add_all([creation_relation_1, creation_relation_2])

        self.session.commit()

        self.assertFalse(is_creator(user_1_id, movement_1_id))
        self.assertFalse(is_creator(user_1_id, movement_2_id))
        self.assertTrue(is_creator(user_2_id, movement_1_id))
        self.assertFalse(is_creator(user_2_id, movement_2_id))
        self.assertFalse(is_creator(user_3_id, movement_1_id))
        self.assertFalse(is_creator(user_3_id, movement_2_id))

    def test_new_movement_by_user(self):
        """Unittest for new_movement_by_user."""
        user = self.create_user(is_admin=True)
        m_name = "Test Movement"
        m_interval = "daily"
        m_short = "This is a movement for testing purposes"
        m_description = (
            "Unit tests are important for a movement creation because they "
            "allow you to verify that the individual units of code that make "
            "up the movement are working correctly. This is important because "
            "it helps to ensure the overall integrity and reliability of the "
            "movement, as well as making it easier to identify and fix any "
            "issues that may arise. Additionally, having a comprehensive set "
            "of unit tests can also make it easier to make changes to the "
            "movement, as you can use the tests to verify that the changes "
            "you have made have not introduced any new problems."
        )
        self.session.commit()
        user_id = user.id

        json = new_movement_by_user(
            user_id=user_id,
            name=m_name,
            interval=m_interval,
            short_description=m_short,
            description=m_description
        )
        self.assertEqual(json['movement']['name'], m_name)
        self.assertEqual(json['movement']['interval'], m_interval)
        self.assertEqual(json['movement']['short_description'], m_short)
        self.assertEqual(json['movement']['description'], m_description)

    def test_remove_creation(self):
        """Unittest for remove_creation."""
        movement = self.create_movement()
        u1 = self.create_user()
        u2 = self.create_user()
        c1 = Creation(u1, movement)
        self.session.add(c1)

        self.session.commit()

        user_1_id = u1.id
        user_2_id = u2.id
        movement_id = movement.id
        assert_json_user = u1.to_json()
        assert_json_movement = movement.to_json()

        # Test removing an existing creation relation
        json_creation = remove_creation(user_1_id, movement_id)
        self.assertDictEqual(assert_json_user, json_creation['user'])
        self.assertDictEqual(assert_json_movement, json_creation['movement'])
        self.assertFalse(json_creation['created'])

        # Test trying to remove none existing subscription
        with self.assertRaises(E.UserIsNotCreator):
            remove_creation(user_2_id, movement_id)
