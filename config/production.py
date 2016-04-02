import os

ADMINS = ['dirk@vermeylen.net']
DEBUG = False
SECRET_KEY = os.urandom(24)
SERVER_NAME = 'localhost:5008'
SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(os.path.dirname(__file__), "../data.sqlite3")
