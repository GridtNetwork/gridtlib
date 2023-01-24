from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy import create_engine

from sqlalchemy_utils import database_exists, create_database

import sys

Base = declarative_base()
Session = scoped_session(sessionmaker())


def init_db_connect(url:str="sqlite:///:memory:") -> None:
    """
    This function initializes the session engine for GridtLib.

    Args:
        url (str): The url to the sql database that should be used.
    """
    
    try:
        if not database_exists(url):
            create_database(url)
    except Exception as ex:
        print("Could not connect to database.")
        print(ex)
        sys.exit(1)

    try:
        engine = create_engine(url)
        Session.configure(bind=engine)
        Base.metadata.create_all(engine)
    except Exception as ex:
        print("Error creating session.")
        print(ex)
        sys.exit(1)
