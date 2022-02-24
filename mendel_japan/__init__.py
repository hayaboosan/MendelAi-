from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os
from flask_login import LoginManager
from flask_bootstraps import Bootstrap
from flask_migrate import Migrate
from sqlalchemy.orm import scoped_session, sessionmaker

from config import engine

db = SQLAlchemy()
session = scoped_session(sessionmaker(
    autocommit=False, autoflush=False, bind=engine))

DB_NAME = 'database.db'
UPLOAD_FOLDER = 'mendel_japan/static/tmp/'
ALLOWED_EXTENSIONS = ['xlsx', 'xlsm', 'xls']


def create_app():
    app = Flask(__name__)
    Bootstrap(app)
    app.config['SECRET_KEY'] = os.urandom(24)

    from config import DATABASE_URI

    app.debug = True
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URI
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    db.init_app(app)
    from .auth.routes import auth
    app.register_blueprint(auth, url_prefix='/')

    from .boars.routes import boars, assets as base_assets
    app.register_blueprint(boars, url_prefix='/boars')
    base_assets.init_app(app)

    from .models import User
    migrate = Migrate(app, db)

    db.create_all(app=app)

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))

    return app
