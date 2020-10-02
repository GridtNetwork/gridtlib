from gridt.basetest import BaseTest
from gridt.models import MovementUserAssociation as MUA, Signal
from .leader import send_signal


class LeaderControllersTest(BaseTest):
    def test_send_signal(self):
        user1 = self.create_user()
        movement1 = self.create_movement()
        mua1 = MUA(movement1, user1, None)
        self.session.add_all([user1, movement1, mua1])
        self.session.commit()

        send_signal(user1.id, movement1.id, "Test.")

        self.session.add_all([user1, movement1, mua1])
        signal = self.session.query(Signal).first()
        self.assertEqual(signal.message, "Test.")
        self.assertEqual(signal.leader, user1)
        self.assertEqual(signal.movement, movement1)

    def test_send_signal_leader_not_in_movement(self):
        user1 = self.create_user()
        movement1 = self.create_movement()
        self.session.add_all([user1, movement1])
        self.session.commit()

        with self.assertRaises(AssertionError):
            send_signal(user1.id, movement1.id, "Test.")
