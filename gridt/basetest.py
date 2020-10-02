"""Base class with helper function that derives from `unittest.TestCase`."""
from unittest import TestCase
import lorem
import random
from sqlalchemy import create_engine
from gridt.db import Session, Base
from gridt.models import User, Movement


class BaseTest(TestCase):
    """Subclass this class to create a test suite."""

    def setUp(self):
        """
        Set up function called before starting a test.

        Initializes the session and creates an sqlite database in memory.
        """
        self.engine = create_engine("sqlite:///:memory:")
        Session.remove()
        Session.configure(bind=self.engine)
        Base.metadata.create_all(self.engine)
        self.session = Session()

    def tearDown(self):
        """
        Close after finishing a test.

        Removes session and clears database.
        """
        self.session.close()
        Base.metadata.create_all(self.engine)

    def create_user(self, generate_bio=False):
        """Create a user in the database."""
        # Usually in tests we number the users, when outputting it is useful to
        # know which user is being represented.
        count = self.session.query(User).count() + 1
        username = str(count) + lorem.sentence()
        email = (
            f"{lorem.sentence().replace(' ', '').replace('.', '')}@test.com"
        )
        password = lorem.sentence()
        bio = ""

        if generate_bio:
            bio = lorem.paragraph()

        user = User(username, email, password, role="user", bio=bio)
        self.session.add(user)
        return user

    def create_movement(self):
        """Create a movement in the database."""
        count = self.session.query(Movement).count() + 1
        name = str(count) + lorem.sentence().split()[0]
        movement = Movement(
            name,
            random.choice(["daily", "twice daily", "weekly"]),
            lorem.sentence(),
            lorem.paragraph(),
        )

        self.session.add(movement)
        return movement
