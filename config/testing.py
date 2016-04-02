import os

DEBUG = False
TESTING = True
SECRET_KEY = 'The Secret Test Key!'
WTF_CSRF_ENABLED = False
SERVER_NAME = 'localhost:5999'
SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(os.path.dirname(__file__), "../data-test.sqlite3")
SQLALCHEMY_TRACK_MODIFICATIONS = False
