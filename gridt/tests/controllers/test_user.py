"""Test for user controller."""
import lorem
from gridt.tests.basetest import BaseTest

from gridt.controllers.user import update_user_bio


class ChangeBioTest(BaseTest):
    """Unittest for changing bio of a user."""

    def test_change_bio(self):
        """Unittest for change_bio."""
        user = self.create_user(generate_bio=True)
        self.session.commit()

        new_bio = lorem.paragraph()
        update_user_bio(user.id, new_bio)

        self.session.add(user)
        self.assertEqual(user.bio, new_bio)
