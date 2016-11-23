import logging
# import os
from config import config
from flask import Flask
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from lib import my_env

bootstrap = Bootstrap()
db = SQLAlchemy()
lm = LoginManager()
lm.login_view = 'main.login'
ns = ""


def create_app(config_name):
    """
    Create an application instance.
    :param config_name: development, test or production
    :return: the configured application object.
    """
    app = Flask(__name__)

    # import configuration
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    # Configure Logger
    my_env.init_loghandler(__name__, app.config.get('LOGDIR'), app.config.get('LOGLEVEL'))

    # initialize extensions
    bootstrap.init_app(app)
    db.init_app(app)
    lm.init_app(app)
    """
    node_params = {
        'wedstrijd': app.config.get('WEDSTRIJD'),
        'o_deelname': app.config.get('O_DEELNAME'),
        'hoofdwedstrijd': app.config.get('HOOFDWEDSTRIJD'),
        'bijwedstrijd': app.config.get('BIJWEDSTRIJD'),
        'deelname': app.config.get('DEELNAME')
    }
    ns.init_graph(**node_params)
    """

    print("4 Line")

    # import blueprints
    from .main import main as main_blueprint
    print('4.2 Line')
    app.register_blueprint(main_blueprint)
    print('4.5 line')
    # configure production logging of errors
    try:
        app.config['PRODUCTION']
    except KeyError:
        # Running in Dev or Test, OK
        pass
    else:
        from logging.handlers import SMTPHandler
        mail_handler = SMTPHandler('127.0.0.1', 'dirk@vermeylen.net', app.config['ADMINS'], 'Application Error')
        mail_handler.setLevel(logging.ERROR)
        app.logger.addHandler(mail_handler)
    print("5 Line")
    return app
