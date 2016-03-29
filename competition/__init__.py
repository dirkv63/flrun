import logging
import os
from .models import graph
from flask import Flask
from flask_bootstrap import Bootstrap

bootstrap = Bootstrap()

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

    # import blueprints
    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    return app

