import platform
import os
from competition import create_app, models_graph as mg
from waitress import serve


# Run Application
if __name__ == "__main__":
    app = create_app('production')
    with app.app_context():
        mg.User().register('dirk', 'olse')
    if platform.node() == "CAA2GKCOR1XXX":
        app.run(host="0.0.0.0", port=5012, debug=True)
    else:
        port = int(os.environ.get("PORT", 80))
        serve(app, port=port)
