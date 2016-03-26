from competition import app
import os
from lib import my_env


# Initialize Environment
projectname = "flaskrun"
# modulename = my_env.get_modulename(__file__)
modulename = "flaskrun"
config = my_env.get_inifile(projectname, __file__)
my_log = my_env.init_loghandler(config, modulename)
my_log.info('Start Application')

# Run Application
app.secret_key = os.urandom(24)
app.run(debug=True, port=5008)
