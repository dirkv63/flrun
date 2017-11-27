import platform
import os
from competition import create_app, models_graph as mg
from waitress import serve


# Run Application
if __name__ == "__main__":
    if platform.node() == "CAA2GKCOR1":
        app = create_app('development')
    else:
        app = create_app('production')

    with app.app_context():
        mg.User().register('dirk', 'olse')

    if platform.node() == "CAA2GKCOR1":
        # app.run(host="0.0.0.0", port=15012, debug=True)
        app.run()
    else:
        serve(app, listen='127.0.0.1:9000')
