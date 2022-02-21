from . import db
from flask_login import UserMixin


class User(db.Model, UserMixin):
    """ユーザーモデル

    ・ユーザー 多 : AIセンター 1
    """
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(150))
    name = db.Column(db.String(50), nullable=False)
    ai_station_id = db.Column(db.Integer, db.ForeignKey('ai_stations.id'))


class Boar(db.Model):
    """雄モデル

    ・雄 多 : 農場 1
    ・雄 多 : 系統 1
    """
    __tablename__ = 'boars'

    id = db.Column(db.Integer, primary_key=True)
    tattoo = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(50), nullable=False)
    birth_on = db.Column(db.Date)
    culling_on = db.Column(db.Date)
    farm_id = db.Column(db.Integer, db.ForeignKey('farms.id'))
    line_id = db.Column(db.Integer, db.ForeignKey('lines.id'))


class Farm(db.Model):
    """農場モデル

    ・農場 1 : 雄 多
    ・農場 多 : AIセンター 1
    """
    __tablename__ = 'farms'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    boar_ids = db.relationship('Boar', backref='farms', lazy=True)
    ai_station_id = db.Column(db.Integer, db.ForeignKey('ai_stations.id'))


class AiStation(db.Model):
    """AIセンターモデル

    ・AIセンター 1 : 農場 多
    ・AIセンター 1 : ユーザー 多
    """
    __tablename__ = 'ai_stations'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    farm_ids = db.relationship('Farm', backref='ai_stations', lazy=True)
    user_ids = db.relationship('User', backref='ai_stations', lazy=True)


class Line(db.Model):
    """系統モデル

    ・系統 1 : 雄 多
    """
    __tablename__ = 'lines'

    id = db.Column(db.Integer, primary_key=True)
    line = db.Column(db.String(50), unique=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    abbreviation = db.Column(db.String(50), unique=True, nullable=False)
    code = db.Column(db.String(50), unique=True)
    boar_ids = db.relationship('Boar', backref='lines', lazy=True)
