"""Functions to get and manipulate database."""
import stripe

from pymongo import MongoClient


def get_db():
    """Return a database object."""
    client = MongoClient("mongodb://admin:therightfit@ds125555." +
                         "mlab.com:25555/the_right_fit")
    db_object = client['the_right_fit']
    return db_object

	