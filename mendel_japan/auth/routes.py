from flask import Blueprint, render_template, flash, redirect, url_for
from ..models import User, AiStation
from werkzeug.security import generate_password_hash, check_password_hash
from .. import db
from flask_login import login_user, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, SelectField
from wtforms.validators import InputRequired, Email, Length, EqualTo


auth = Blueprint('auth', __name__,)


@auth.route('/')
@login_required
def index() -> str:
    """
    トップページを返す

    Returns:
        str: HTML
    """
    return redirect(url_for('boars.index'))


class SignUpForm(FlaskForm):
    """
    ユーザー登録用フォーム

    Attributes:
        email: str, メールアドレス, 入力必須, メールのフォーマットに適合させる
        name: str, ユーザー名, 入力必須, 10文字以下
        password: password, パスワード, 入力必須
        confirm: password, パスワード確認, 入力必須, パスワードと一致させる
        submit: submit, 送信, ボタンタイトルはtemplatesで設定
    """
    email = StringField('メールアドレス', validators=[
        InputRequired('必須です'),
        Email(message='有効なメールアドレスではありません')])
    name = StringField('ユーザー名', validators=[
        InputRequired('必須です'),
        Length(max=10, message='10文字以内で入力してください')])
    password = PasswordField('パスワード', validators=[
        InputRequired('必須です')])
    confirm = PasswordField('パスワード確認', validators=[
        InputRequired('必須です'),
        EqualTo('password', message='パスワードと一致しません')])
    ai_station_id = SelectField('AIセンター', coerce=int)
    submit = SubmitField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._set_ai_stations()

    def _set_ai_stations(self) -> None:
        """AIセンターモデルのデータを選択肢として表示させる

        Args:
            self (SignUpForm): 入力フォーム
        """
        ai_stations: AiStation = AiStation.query.order_by(AiStation.id).all()
        self.ai_station_id.choices = \
            [(ai_station.id, ai_station.name) for ai_station in ai_stations]


class LoginForm(FlaskForm):
    """
    ログイン用フォーム

    Attributes:
        email: str, メールアドレス, 入力必須, メールのフォーマットに適合させる
        password: password, パスワード, 入力必須
        submit: submit, 送信, ボタンタイトルはtemplatesで設定
    """
    email = StringField('メールアドレス', validators=[
        InputRequired('必須です'),
        Email(message='有効なメールアドレスではありません')])
    password = PasswordField('パスワード', validators=[
        InputRequired('必須です')])
    submit = SubmitField()


@auth.route('/login', methods=['GET', 'POST'])
def login() -> str:
    """
    ログインする
    入力したメールアドレスが既存のユーザーのもので、
    入力したパスワードがそのゆーざーのものである場合、
    ログインして雄一覧ページへ遷移する

    Returns:
        str: HTML
    """
    form: LoginForm = LoginForm()
    if form.validate_on_submit():
        email: str = form.email.data
        password: str = form.password.data
        user: User = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            flash('ログインしました', category='success')
            login_user(user, remember=True)
            return redirect(url_for('boars.index'))
        else:
            flash('ログイン情報を確認してください', category='error')

    return render_template('./auth/login.html', user=current_user, form=form)


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('ログアウトしました', category='success')
    return redirect(url_for('auth.login'))


@auth.route('/sign-up', methods=['GET', 'POST'])
def sign_up():
    form = SignUpForm()
    if form.validate_on_submit():
        registered_user = User.query.filter_by(
            email=form.email.data).first()
        if registered_user:
            flash('そのメールアドレスは登録済みです', category='error')
        else:
            user = commit_user(form)
            login_user(user, remember=True)
            flash('ユーザーを登録しました', category='success')
            return redirect(url_for('auth.index'))
    return render_template("./auth/sign_up.html", user=current_user, form=form)


@auth.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    user = User.query.get(id)
    form = SignUpForm(obj=user)
    if form.validate_on_submit():
        user = commit_user(form, id)
        flash('ユーザーを更新しました', category='success')
        return redirect(url_for('boars.index'))
    return render_template("./auth/edit.html", user=current_user, form=form)


def commit_user(form, id=None):
    if id:
        user = User.query.get(id)
    else:
        user = User()
    db.session.commit()
    user.name = form.name.data
    user.email = form.email.data
    user.password = generate_password_hash(form.password.data, method='sha256')
    if id is None:
        db.session.add(user)
    db.session.commit()
    return user
