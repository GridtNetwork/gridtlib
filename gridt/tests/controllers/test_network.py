"""Test for the network controller."""
from gridt.tests.basetest import BaseTest

from gridt.controllers.user import (
    register,
    verify_password_for_email,
)
from gridt.controllers.network import get_network_data
from gridt.controllers.creation import new_movement_by_user
from gridt.controllers.subscription import new_subscription
from gridt.controllers.leader import send_signal
from gridt.models import UserToUserLink

from freezegun import freeze_time
from datetime import datetime
from itertools import combinations


class NetworkControllerUnitTests(BaseTest):
    """Unittests for network controller."""

    def test_get_network_data_small(self):
        """Unittest for get_network data case 1 subscriber."""
        movement = self.create_movement()
        user = self.create_user()
        self.create_subscription(movement, user)
        self.session.commit()

        movement_id = movement.id
        user_id = user.id

        expected = {'edges': [], 'nodes': [(user_id, None)]}
        self.assertEqual(get_network_data(movement_id), expected)

    def test_get_network_data_empty(self):
        """Unittest for get_network data case empty."""
        movement = self.create_movement()
        movement_id = movement.id
        self.session.commit()
        expected = {'edges': [], 'nodes': []}
        self.assertEqual(get_network_data(movement_id), expected)

    def test_get_network_data_large(self):
        """Unittest for get_network data case 5 subscribers."""
        movement = self.create_movement()
        users = []
        for _ in range(5):
            user = self.create_user()
            self.create_subscription(movement, user)
            users.append(user)
        for i in range(5):
            follower = users[i]
            leader = users[(i + 1) % 5]
            link = UserToUserLink(movement, follower, leader)
            self.session.add(link)

        self.session.commit()
        movement_id = movement.id

        expected = {
            'edges': [(i, (i % 5) + 1) for i in range(1, 6)],
            'nodes': [(i, None) for i in range(1, 6)]
        }
        self.assertEqual(get_network_data(movement_id), expected)


class TestUserStoriesNetworkController(BaseTest):
    """Network data related user stories."""

    def test_get_network_data(self):
        """
        As an admin I would like to be able to retrieve network data for demos.

        Steps:
         - register an admin,
         - create a movement,
         - register users,
         - users subscribe to movement
         - (some) users create signals
         - get network data
        """
        # 1. Register admin
        admin_email = 'antonin.thioux@gmail.com'
        admin_password = 'password123'
        register('Antonin', admin_email, admin_password, is_admin=True)
        antonin_id = verify_password_for_email(admin_email, admin_password)

        # 2. Create movement
        title = "Meditate everyday"
        create_json = new_movement_by_user(antonin_id, title, 'daily')
        movement_json = create_json['movement']
        movement_id = movement_json['id']

        # 3. Register 4 users
        user_ids = []
        for i in range(4):
            email = f'user.{i}@gmail.com'
            password = 'insecure'
            register(f'User_{i}', email, password)
            user_ids.append(verify_password_for_email(email, password))

        # 4. Users subscribe to movement
        for user_id in user_ids:
            new_subscription(user_id, movement_id)

        # 5. User 1 and 2 create signals
        earlier = datetime(2023, 4, 7, 17, 0)
        later = datetime(2023, 4, 7, 17, 30)
        with freeze_time(earlier):
            hello = "Hello World"
            send_signal(user_ids[0], movement_id, message=hello)
        with freeze_time(later):
            namaste = "Namaste"
            send_signal(user_ids[1], movement_id, message=namaste)

        network_data = get_network_data(movement_id)
        nodes = network_data['nodes']
        node_1 = {'message': hello, 'time_stamp': str(earlier.astimezone())}
        node_2 = {'message': namaste, 'time_stamp': str(later.astimezone())}
        expected_nodes = (
            [(antonin_id, None)] +
            [(user_ids[0], node_1)] +
            [(user_ids[1], node_2)] +
            [(user_id, None) for user_id in user_ids[2:]]
        )
        self.assertListEqual(sorted(expected_nodes), sorted(nodes))

        edges = network_data['edges']
        undirected = list(combinations([antonin_id, *user_ids], 2))
        directed = undirected + [(b, a) for a, b in undirected]
        self.assertListEqual(sorted(directed), sorted(edges))
        self.assertNotEqual(sorted(undirected), sorted(edges))
