import os
# basedir = os.path.abspath(os.path.dirname(__file__))
# print('Basedir: {b}'.format(b=basedir))

# Be careful: Variable names need to be UPPERCASE


class Config:
    SECRET_KEY = os.urandom(24)

    # Config values from flaskrun.ini
    LOGDIR = "C:\\Temp\\Log"

    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    DEBUG = True
    LOGLEVEL = "debug"
    # SERVER_NAME = '0.0.0.0:5012'
    # SERVER_NAME = 'localhost:50120'


class TestingConfig(Config):
    DEBUG = False
    # Set Loglevel to warning or worse (error, fatal) for readability
    LOGLEVEL = "error"
    TESTING = True
    SECRET_KEY = 'The Secret Test Key!'
    WTF_CSRF_ENABLED = False
    SERVER_NAME = 'localhost:5999'


class ProductionConfig(Config):
    ADMINS = ['dirk@vermeylen.net']
    LOGLEVEL = "warning"
    # SERVER_NAME = 'localhost:5008'
    DEBUG = False


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,

    'default': DevelopmentConfig
}
