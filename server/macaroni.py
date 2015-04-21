import os
import logging

from flask_limiter import Limiter

# internal imports
from app_and_db import app, db
from config import ConfigClass

# modules aka blueprints
from api.views import api_blueprint
from users.views import users_blueprint
from web.views import site_blueprint

# Configure logging
logger = logging.getLogger()

logger.setLevel(ConfigClass.flask_log_level)

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(module)s %(funcName)s : %(message)s')

fh = logging.FileHandler(ConfigClass.flask_logfile)
fh.setLevel(ConfigClass.flask_log_level)
fh.setFormatter(formatter)
logger.addHandler(fh)

sh = logging.StreamHandler()
sh.setLevel(ConfigClass.flask_log_level)
sh.setFormatter(formatter)
logger.addHandler(sh)

# Initialize Flask Limiter extension
limiter = Limiter(app, headers_enabled=ConfigClass.xrate_limit_headers_enabled, 
    strategy='fixed-window-elastic-expiry',
    storage_uri=ConfigClass.redis_cache_uri)

# set rate limits for each module/blueprint
limiter.limit("1/second;10/minute")(api_blueprint)
limiter.limit("1/second;10/minute")(users_blueprint)
limiter.limit("1/second;10/minute")(site_blueprint)

# register blueprints
app.register_blueprint(api_blueprint)
app.register_blueprint(users_blueprint)
app.register_blueprint(site_blueprint)


if __name__ == '__main__':
	if ConfigClass.debug_mode:
	    app.run(host=ConfigClass.debug_host, port=ConfigClass.debug_port, debug=True)
	else:
		app.run(debug=False)
