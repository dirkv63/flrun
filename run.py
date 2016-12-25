#!/usr/bin/env python
# import logging
import os
from competition import create_app, models_graph as mg
# from lib import my_env
from waitress import serve


# Run Application
if __name__ == "__main__":
    app = create_app('development')
    with app.app_context():
        mg.User().register('dirk', 'olse')
    # app.run()
    port = int(os.environ.get("PORT", 5012))
    serve(app, port=port)
