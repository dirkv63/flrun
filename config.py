import os
# basedir = os.path.abspath(os.path.dirname(__file__))
# print('Basedir: {b}'.format(b=basedir))

# Be careful: Variable names need to be UPPERCASE


class Config:
    SECRET_KEY = os.urandom(24)

    # Config values from flaskrun.ini
    LOGDIR = "C:\\Temp\\Log"
    # Neo4J Attributes
    N4J_USER = "neo4j"
    N4J_PWD = "_m8z8IpJUPyR"
    N4J_DB = "stratenloop15.db"
    # OrgType
    WEDSTRIJD = "De organizatie heeft één hoofdwedstrijd en kan één of meer bijwedstrijden hebben."
    O_DEELNAME = "Dit is een organizatie waar elke deelnemer en elke medewerker punten krijgt."
    # RaceType
    HOOFDWEDSTRIJD = "De wedstrijd moet in OLSE shirt gelopen worden. Puntenverdeling: 50, 45, 40. " \
                     "Vanaf dan per punt 39, 38, 37, ..."
    BIJWEDSTRIJD = "De wedstrijd moet in OLSE shirt gelopen worden. Iedereen krijgt evenveel punten. " \
                   "Het aantal punten is als zou de deelnemer de laatste OLSE'er geweest zijn in de hoofdwedstrijd."
    DEELNAME = "Elke deelnemer krijgt 20 punten. Dit geldt ook voor medewerkers, die niet aan een wedstrijd hebben" \
               "deelgenomen."

    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    DEBUG = True
    LOGLEVEL = "info"
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
    SERVER_NAME = 'localhost:5008'
    DEBUG = False


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,

    'default': DevelopmentConfig
}
