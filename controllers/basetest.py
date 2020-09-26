from unittest import TestCase
from sqlalchemy import create_engine
from db import Session, Base


class BaseTest(TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        Session.remove()
        Session.configure(bind=self.engine)
        Base.metadata.create_all(self.engine)
        self.session = Session()

    def tearDown(self):
        self.session.close()
        Base.metadata.create_all(self.engine)
