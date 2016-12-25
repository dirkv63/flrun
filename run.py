#!/usr/bin/env python
# import logging
import os
from competition import create_app, db
from competition.models_sql import User
# from lib import my_env
from waitress import serve


# Run Application
if __name__ == "__main__":
    app = create_app('development')
    with app.app_context():
        db.create_all()
        if User.query.filter_by(username='dirk').first() is None:
            User.register('dirk', 'olse')
    # app.run()
    port = int(os.environ.get("PORT", 5012))
    serve(app, port=port)
