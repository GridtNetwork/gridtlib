from freezegun import freeze_time
from unittest import skip

from gridt.tests.basetest import BaseTest
from gridt.models import Movement, Subscription, MovementToMovementLink

from gridt.controllers.leader import send_signal
from gridt.controllers.movements import get_movement


class MovementControllerUnitTests(BaseTest):
    
    def test_get_movement(self):
        movement = Movement(
            "movement1",
            "daily",
            short_description="Hi",
            description="A long description",
        )
        user_1 = self.create_user()
        user_2 = self.create_user(generate_bio=True)
        subscription_1 = Subscription(user_1, movement)
        subscription_2 = Subscription(user_2, movement)
        movement_to_movement_link1 = MovementToMovementLink(movement, user_1, user_2)
        movement_to_movement_link1 = MovementToMovementLink(movement, user_2, user_1)

        self.session.add_all([movement, subscription_1, subscription_2, movement_to_movement_link1, movement_to_movement_link1])
        self.session.commit()

        u1_id, u2_id, m_id = user_1.id, user_2.id, movement.id

        now = "1995-01-15 12:00:00+01:00"
        later = "1996-03-15 08:00:00+01:00"

        message = "This is a message"

        with freeze_time(now, tz_offset=1):
            send_signal(u1_id, m_id)
        with freeze_time(later, tz_offset=1):
            send_signal(u2_id, m_id, message=message)
        
        self.session.add_all([user_1, user_2, movement])
        user_dict = user_1.to_json()
        user_dict["last_signal"] = {"time_stamp": now}
        expected = {
            "id": 1,
            "name": "movement1",
            "short_description": "Hi",
            "description": "A long description",
            "interval": "daily",
            "subscribed": True,
            "leaders": [user_dict],
            "last_signal_sent": {
                "time_stamp": "1996-03-15 08:00:00+01:00",
                "message": "This is a message"
            },
        }
        self.assertEqual(get_movement(movement.id, user_2.id), expected)


class MovementControllerIntergrationTests(BaseTest):
    @skip
    def test_create_and_get_movement(self):
        pass
