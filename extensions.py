from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_talisman import Talisman
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf import CSRFProtect

# Central place for extension instances to avoid circular imports
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
# Talisman will be initialized in app factory to set CSP and other headers
talisman = Talisman()
limiter = Limiter(key_func=get_remote_address, default_limits=["200/day", "50/hour"]) 
csrf = CSRFProtect()
