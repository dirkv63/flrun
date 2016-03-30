import logging
import os
# from .models import graph
from flask import Flask
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

bootstrap = Bootstrap()
db = SQLAlchemy()
lm = LoginManager()
lm.login_view = 'main.login'


def create_app(config_name):
    """
    Create an application instance.
    :param config_name: development, test or production
    :return: the configured application object.
    """
    app = Flask(__name__)

    # import configuration
    cfg = os.path.join(os.getcwd(), 'config', config_name + '.py')
    logging.debug("Config file: {cfg}".format(cfg=cfg))
    app.config.from_pyfile(cfg)

    # initialize extensions
    bootstrap.init_app(app)
    db.init_app(app)
    lm.init_app(app)

    # import blueprints
    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    return app
