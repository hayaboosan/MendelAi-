from . import db
from flask_login import UserMixin


class User(db.Model, UserMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(150))
    name = db.Column(db.String(50), nullable=False)


class Boar(db.Model, UserMixin):
    __tablename__ = 'boars'

    id = db.Column(db.Integer, primary_key=True)
    tattoo = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(50), nullable=False)
    birth_on = db.Column(db.Date)
    line = db.Column(db.String(50), nullable=False)
    culling_on = db.Column(db.Date)
