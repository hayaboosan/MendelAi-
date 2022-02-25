from . import db, session
from flask_login import UserMixin
from sqlalchemy import and_, func, desc


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
    ・雄 1 : 状態 多
    """
    __tablename__ = 'boars'

    id = db.Column(db.Integer, primary_key=True)
    tattoo = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(50), nullable=False)
    birth_on = db.Column(db.Date)
    culling_on = db.Column(db.Date)
    farm_id = db.Column(db.Integer, db.ForeignKey('farms.id'))
    line_id = db.Column(db.Integer, db.ForeignKey('lines.id'))
    status_ids = db.relationship('Status', backref='boars', lazy=True)

    def status_ids_list(self):
        return [x.id for x in self.status_ids]

    def all_statuses(self):
        return session.query(Status) \
            .filter(Status.id.in_(self.status_ids_list())) \
            .order_by(desc(Status.start_on)).limit(5).all()

    def latest_status(self):
        latest_status_date = session.query(func.max(Status.start_on)) \
            .filter(Status.id.in_(self.status_ids_list())).first()[0]

        return session.query(Status) \
            .filter(and_(
                Status.id.in_(self.status_ids_list()),
                Status.start_on == latest_status_date
            )).first()

    def ai_station(self):
        return AiStation.query.get(
            Farm.query.get(self.farm_id).ai_station_id)

    def line(self):
        return Line.query.get(self.line_id)

    def farm(self):
        return Farm.query.get(self.farm_id)


class Farm(db.Model):
    """農場モデル

    ・農場 1 : 雄 多
    ・農場 多 : AIセンター 1
    """
    __tablename__ = 'farms'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    abbreviation = db.Column(db.String(50), unique=True)
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
    abbreviation = db.Column(db.String(50), unique=True)
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


class Status(db.Model):
    """状態モデル

    ・状態 多 : 雄 1
    """
    __tablename__ = 'statuses'

    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.String(50), nullable=False)
    reason = db.Column(db.String(50))
    start_on = db.Column(db.Date)
    boar_id = db.Column(db.Integer, db.ForeignKey('boars.id'))
