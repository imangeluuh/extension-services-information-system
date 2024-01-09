from flask import Flask
import psycopg2
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_wtf import CSRFProtect
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_ckeditor import CKEditor
from flask_restx import Api
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_mail import Mail
from flask_caching import Cache
from config import Config
import os

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
login_manager = LoginManager()
csrf = CSRFProtect()
bcrypt = Bcrypt()
ckeditor = CKEditor()
mail = Mail()
cache = Cache()
api = Api(doc='/docs', decorators=[csrf.exempt])

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    bcrypt.init_app(app)
    ckeditor.init_app(app)
    mail.init_app(app)
    
    app.config['CACHE_TYPE'] = 'simple'
    cache.init_app(app)

    CORS(app)

    app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, "media")

    # Register the root route from views.py
    app.add_url_rule("/", view_func=home)
    
    api.init_app(app)

    from .Api.resources import ns
    api.add_namespace(ns)

    from .main.routes import bp as main_bp
    app.register_blueprint(main_bp)

    from .admin.admin import bp as admin_bp
    app.register_blueprint(admin_bp, url_prefix="/admin")

    from .auth.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix="/auth") 

    from .programs.programs import bp as programs_bp
    app.register_blueprint(programs_bp, url_prefix='/') 

    from .announcement.announcement import bp as announcement_bp
    app.register_blueprint(announcement_bp, url_prefix='/')

    from .evaluation.evaluation import bp as evaluation_bp
    app.register_blueprint(evaluation_bp, url_prefix='/')

    from .user import bp as user_bp
    app.register_blueprint(user_bp, url_prefix='/')

    from app.errors import bp as errors_bp
    app.register_blueprint(errors_bp)

    return app


# route where user will be redirected if not logged in
# login_manager.login_view = [enter route here]
# limiter = Limiter(get_remote_address, app=app, default_limits=['5 per day'])

from app import models
from .main.routes import home
