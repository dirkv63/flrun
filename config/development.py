import os

DEBUG = True
SECRET_KEY = os.urandom(24)
SERVER_NAME = 'localhost:5008'
SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(os.path.dirname(__file__), "../data-dev.sqlite3")
SQLALCHEMY_TRACK_MODIFICATIONS = True
