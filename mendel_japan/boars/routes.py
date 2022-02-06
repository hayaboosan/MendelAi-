from __future__ import annotations
from flask import (
    Blueprint, render_template, flash, redirect, url_for, request, jsonify,
    wrappers)
from flask import current_app as app
from flask_assets import Bundle, Environment
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
import flask_sqlalchemy


import os
from typing import TypeVar
from wtforms import (
    StringField, DateField, validators, SubmitField, FileField, RadioField,
    BooleanField, SelectField)
from werkzeug.utils import secure_filename
import json
from sqlalchemy import and_, asc


from mendel_japan import db, ALLOWED_EXTENSIONS, UPLOAD_FOLDER
from mendel_japan.models import Boar, Farm
from mendel_japan.boars import exporter, importer

boars = Blueprint('boars', __name__,)
js = Bundle('javascript/boars.js', output='javascript/main.js')
assets = Environment(app)
assets.register('main_js', js)

FileObject = TypeVar('FileObject')


class BoarForm(FlaskForm):
    tattoo = StringField('タトゥー', validators=[
        validators.InputRequired('必須です'),
        validators.Length(max=10, message='10文字以内で入力してください')])
    name = StringField('雄ID', validators=[
        validators.InputRequired('必須です'),
        validators.Length(max=10, message='10文字以内で入力してください')])
    line = StringField('系統', validators=[
        validators.InputRequired('必須です'),
        validators.Length(max=10, message='10文字以内で入力してください')])
    birth_on = DateField('生年月日', validators=[
        validators.Optional(strip_whitespace=True)])
    culling_on = DateField('淘汰日', validators=[
        validators.Optional(strip_whitespace=True)])
    farm_id = SelectField('農場', coerce=int)
    submit = SubmitField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._set_farms()

    def _set_farms(self: BoarForm) -> None:
        """
        Farmモデルのデータを選択肢として表示させる

        Args:
            self (BoarForm): 入力フォーム
        """
        farms: Farm = Farm.query.order_by(asc(Farm.id)).all()
        self.farm_id.choices = [(farm.id, farm.name) for farm in farms]


class BoarUpload(FlaskForm):
    file = FileField('', validators=[
        validators.InputRequired('必須です')])
    farm_id = SelectField('農場', coerce=int)
    submit = SubmitField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._set_farms()

    def _set_farms(self: BoarForm) -> None:
        """
        Farmモデルのデータを選択肢として表示させる

        Args:
            self (BoarForm): 入力フォーム
        """
        farms: Farm = Farm.query.order_by(asc(Farm.id)).all()
        self.farm_id.choices = [(farm.id, farm.name) for farm in farms]


class BoarDownload(FlaskForm):
    enrollment_status = \
        RadioField('在籍状況', choices=[
            ('all', '全て'),
            ('alive_only', '在籍中のみ'),
            ('culled_only', '淘汰済みのみ'),
        ], validators=[validators.InputRequired()])
    m_line = BooleanField('D')
    n_line = BooleanField('TL')
    l_line = BooleanField('LL')
    z_line = BooleanField('TW')
    jl_line = BooleanField('L')
    jw_line = BooleanField('W')
    submit = SubmitField()


@boars.route('/', methods=['GET', 'POST'])
# @login_required
def index() -> str:
    """
    /boars/
    登録済みの雄一覧を表示

    Returns:
        str: html
    """
    boars: Boar = Boar.query.all()
    return render_template(
        './boars/index.html', user=current_user, boars=boars, farms=Farm.query)


def search_date(date, start_or_end):
    if date:
        return date
    elif start_or_end == 'start':
        return '0001-01-01'
    else:
        return '3000-01-01'


@ boars.route('/create', methods=['GET', 'POST'])
# @login_required
def create() -> str:
    """
    新規雄情報を作成する
    既に登録されているtattooの場合エラーを表示する
    登録が完了したら雄一覧へリダイレクトする

    Returns:
        str: html
    """
    form: BoarForm = BoarForm()
    if form.validate_on_submit():
        if Boar.query.filter_by(tattoo=form.tattoo.data).first():
            flash('そのタトゥーは登録済みです', category='error')
        else:
            commit_boar(form)
            flash('新規雄を登録しました', category='success')
            return redirect(url_for('boars.index'))
    return render_template('./boars/create.html', user=current_user, form=form)


@ boars.route('/<int:id>/edit', methods=['GET', 'POST'])
# @login_required
def edit(id: int) -> str:
    """
    既存の雄情報を編集する
    tattooを修正して、他の既存の雄と重複する場合はエラーを表示
    編集が完了したら雄一覧へリダイレクトする

    Args:
        id (int): 対象の雄のboarsテーブルのid

    Returns:
        str: html
    """
    boar: Boar = Boar.query.get(id)
    form: BoarForm = BoarForm(obj=boar)
    if form.validate_on_submit():
        registered_boar: Boar = Boar.query.filter_by(
            tattoo=form.tattoo.data).first()
        if registered_boar is boar or registered_boar is None:
            commit_boar(form, id)
            flash('雄情報を更新しました', category='success')
            return redirect(url_for('boars.index'))
        else:
            flash('そのタトゥーは登録済みです', category='error')
            return render_template(
                './boars/edit.html', user=current_user, form=form)
    else:
        return render_template(
            './boars/edit.html', user=current_user, form=form)


def commit_boar(form: BoarForm, id: int = None) -> None:
    """
    boarsテーブルにコミットする
    既にidがある場合は更新
    ない場合は新規で登録

    Args:
        form (BoarForm): ユーザーがフォームに入力した内容
        id (int, optional): boarsテーブルのid. Defaults to None.
    """
    boar: Boar = Boar.query.get(id) if id else Boar()
    boar.tattoo = form.tattoo.data
    boar.name = form.name.data
    boar.line = form.line.data
    boar.birth_on = form.birth_on.data
    boar.culling_on = form.culling_on.data
    boar.farm_id = form.farm_id.data
    if id is None:
        db.session.add(boar)
    db.session.commit()


@ boars.route('/upload', methods=['GET', 'POST'])
# @login_required
def upload() -> str:
    """
    boarsテーブルに雄を一括登録する
    アップロードできるのはExcel形式のファイルのみ
    アップロードが完了したら雄一覧へリダイレクトする

    Returns:
        str: html
    """
    form: BoarUpload = BoarUpload()
    if form.validate_on_submit():
        file: request = request.files['file']
        if file and allowed_file(file.filename):
            save_and_import(file, form.farm_id.data)
            return redirect(url_for('boars.index'))
        else:
            flash(
                f'アップロードできるファイル形式は{ALLOWED_EXTENSIONS}です',
                'error')
    return render_template('./boars/upload.html', user=current_user, form=form)


def allowed_file(filename: str) -> bool:
    """
    アップロードフィアルの拡張子をチェック

    Args:
        filename (str): アップロードファイル名

    Returns:
        bool: ファイル名にドットが入っていて、指定の拡張子であるか
    """
    extension: str = filename.rsplit('.', 1)[1].lower()
    return '.' in filename and extension in ALLOWED_EXTENSIONS


def save_and_import(file: FileObject, farm_id: int) -> None:
    """
    アップロードしたファイルをtmpディレクトリに一時保管
    ファイル内容をDBに登録する

    Args:
        file (FileObject): アップロードファイル
    """
    filename: str = secure_filename(file.filename)
    file_path: str = os.path.join(UPLOAD_FOLDER, filename)
    file.save(file_path)
    importer.import_boar_list(file_path, filename, farm_id)


@ boars.route('/delete-boar', methods=['POST'])
# @login_required
def delete_boar() -> jsonify:
    """
    雄を削除する
    ・boars.jsからデータを受け取り削除処理
    ・削除処理完了後boars.jsにて表示を削除

    Returns:
        jsonify: 空のJSON
    """
    data: dict = json.loads(request.data)
    boarId: int = data['boarId']
    boar: Boar = Boar.query.get(boarId)
    if boar:
        db.session.delete(boar)
        db.session.commit()
    return jsonify({})


@boars.route('/download', methods=['GET', 'POST'])
# @login_required
def download() -> str | wrappers.Response:
    """
    雄リストダウンロードページ
    ・選択した在籍状況と系統の雄リストを作成
    ・雄リストをExcelファイルにエクスポート
    ・Excelファイルをダウンロード

    Returns:
        str: HTML | flask.wrappers.Response: レスポンス(Excelファイル)
    """
    form: BoarDownload = BoarDownload()
    if form.validate_on_submit():
        boar_ids: list = check_enrollment_status(form)
        boars_query: list = check_line(boar_ids, form)
        return exporter.downloadExcel(boars_query)
    return render_template(
        './boars/download.html', user=current_user, form=form)


def check_enrollment_status(form: BoarDownload) -> list:
    """
    選択した在籍状況の雄id(インデックス番号)をリストで返す

    Args:
        form (BoarDownload): フォーム入力内容

    Returns:
        list: 雄id(インデックス番号)
    """
    enrollment_status: str = form.enrollment_status.data
    if enrollment_status == 'alive_only':
        boar_list: list = Boar.query.filter(Boar.culling_on.is_(None)).all()
    elif enrollment_status == 'culled_only':
        boar_list: list = Boar.query.filter(
            Boar.culling_on == Boar.culling_on).all()
    else:
        boar_list: list = Boar.query.all()
    return [x.id for x in boar_list]


def check_line(
        boar_ids: list, form: BoarDownload) -> flask_sqlalchemy.BaseQuery:
    """
    選択した在籍状況と系統の雄を返す

    Args:
        boar_ids (list): 雄id(インデックス番号)
        form (BoarDownload): フォーム入力内容

    Returns:
        list: 雄一覧
    """
    lines: list = []
    if form.m_line.data:
        lines.append('MMMM')
    if form.n_line.data:
        lines.append('NNNN')
    if form.l_line.data:
        lines.append('LLLL')
    if form.z_line.data:
        lines.append('ZZZZ')
    return Boar.query.filter(and_(
        Boar.id.in_(boar_ids), Boar.line.in_(lines),))


# TODO: 状態モデルの作成と雄モデルの接続
