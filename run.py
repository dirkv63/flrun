#!/usr/bin/env python
import logging
from competition import create_app, db
from competition.models_sql import User
from competition.models_graph import init_graph
from lib import my_env


# Run Application
if __name__ == "__main__":
    app = create_app('development')
    init_graph(config)
    with app.app_context():
        db.create_all()
        if User.query.filter_by(username='dirk').first() is None:
            User.register('dirk', 'olse')
    app.run()
