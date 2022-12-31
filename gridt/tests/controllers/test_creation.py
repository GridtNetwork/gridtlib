from ..basetest import BaseTest

from gridt.controllers.creation import (
    _get_creation,
    is_creator,
    new_creation,
    on_creation,
    _notify_creation_listeners,
    _on_create_events,
    remove_creation,
    on_remove_creation,
    _notify_remove_creation_listeners,
    _on_remove_creation_events
)
import gridt.exc as E
from gridt.models.creation import Creation

class CreationControllerTest(BaseTest):

    def test_helper_get_creation(self):
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

    def test_on_creation(self):
        def dummy_func():
            pass
        on_creation(dummy_func)
        self.assertIn(dummy_func, _on_create_events)
        _on_create_events.remove(dummy_func)
    
    def test_notify_creation_listeners(self):
        # Remove all the events in the event listener
        temp = _on_create_events.copy()
        for event in temp:
            _on_create_events.remove(event)

        def dummy_func(x, y):
            dummy_func.has_been_called = True
            assert(x == 3)
            assert(y == 7)

        dummy_func.has_been_called = False
        _on_create_events.add(dummy_func)
        _notify_creation_listeners(3, 7)
        self.assertTrue(dummy_func.has_been_called)

        # Restore event listener to want it was previously
        for event in temp:
            _on_create_events.add(event)
        _on_create_events.remove(dummy_func)

    def test_new_creation(self):
        user = self.create_user()
        movement = self.create_movement()

        self.session.commit()

        user_id = user.id
        movement_id = movement.id
        assert_json_user = user.to_json()
        assert_json_movement = movement.to_json()

        json_creation = new_creation(user_id, movement_id)
        self.assertDictEqual(assert_json_user, json_creation['user'])
        self.assertDictEqual(assert_json_movement, json_creation['movement'])
        self.assertTrue(json_creation['created'])

    def test_on_remove_creation(self):
        def dummy_func1():
            pass
        def dummy_func2():
            pass
        on_remove_creation(dummy_func1)
        self.assertIn(dummy_func1, _on_remove_creation_events)
        self.assertNotIn(dummy_func2, _on_remove_creation_events)
        _on_remove_creation_events.remove(dummy_func1)

    def test_notify_remove_creation_listeners(self):
        # Remove all the events in the event listener
        temp = _on_remove_creation_events.copy()
        for event in temp:
            _on_remove_creation_events.remove(event)

        def dummy_func(x, y):
            dummy_func.has_been_called = True
            assert(x == 123)
            assert(y == 987)

        _on_remove_creation_events.add(dummy_func)
        _notify_remove_creation_listeners(123, 987)

        # Restore event listener to want it was previously
        for event in temp:
            _on_remove_creation_events.add(event)
        _on_remove_creation_events.remove(dummy_func)

    def test_remove_creation(self):
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

