from __future__ import annotations
from flask import (
    Blueprint, render_template, flash, redirect, url_for, request, jsonify,
    wrappers)
from flask import current_app as app
from flask_assets import Bundle, Environment
from flask_login import login_required, current_user
import flask_sqlalchemy


import os
from typing import TypeVar
from werkzeug.utils import secure_filename
import json
from sqlalchemy import and_


from mendel_japan import db, ALLOWED_EXTENSIONS, UPLOAD_FOLDER
from mendel_japan.models import Boar, Farm, AiStation
from mendel_japan.boars import exporter, forms, importer


boars = Blueprint('boars', __name__,)
js = Bundle('javascript/boars.js', output='javascript/main.js')
assets = Environment(app)
assets.register('main_js', js)

FileObject = TypeVar('FileObject')


@boars.route('/', methods=['GET', 'POST'])
@login_required
def index() -> str:
    """登録済みの雄一覧を表示

    ・ログイン中のユーザーが所属しているAIセンター管轄の農場IDをリストに格納
    ・管轄農場に所属している雄を全て表示

    Returns:
        str: html
    """
    farm_ids = [
        x.id for x in AiStation.query.get(current_user.ai_station_id).farm_ids]
    boars: Boar = Boar.query.filter(Boar.farm_id.in_(farm_ids)).all()
    return render_template(
        './boars/index.html', user=current_user, boars=boars, farms=Farm.query)


@ boars.route('/create', methods=['GET', 'POST'])
@login_required
def create() -> str:
    """
    新規雄情報を作成する
    既に登録されているtattooの場合エラーを表示する
    登録が完了したら雄一覧へリダイレクトする

    Returns:
        str: html
    """
    form: forms.BoarForm = forms.BoarForm()
    if form.validate_on_submit():
        if Boar.query.filter_by(tattoo=form.tattoo.data).first():
            flash('そのタトゥーは登録済みです', category='error')
        else:
            commit_boar(form)
            flash('新規雄を登録しました', category='success')
            return redirect(url_for('boars.index'))
    return render_template('./boars/create.html', user=current_user, form=form)


@ boars.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
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
    form: forms.BoarForm = forms.BoarForm(obj=boar)
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


def commit_boar(form: forms.BoarForm, id: int = None) -> None:
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
@login_required
def upload() -> str:
    """
    boarsテーブルに雄を一括登録する
    アップロードできるのはExcel形式のファイルのみ
    アップロードが完了したら雄一覧へリダイレクトする

    Returns:
        str: html
    """
    form: forms.BoarUpload = forms.BoarUpload()
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
@login_required
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
@login_required
def download() -> str | wrappers.Response:
    """
    雄リストダウンロードページ
    ・選択した在籍状況と系統の雄リストを作成
    ・雄リストをExcelファイルにエクスポート
    ・Excelファイルをダウンロード

    Returns:
        str: HTML | flask.wrappers.Response: レスポンス(Excelファイル)
    """
    form: forms.BoarDownload = forms.BoarDownload()
    if form.validate_on_submit():
        boar_ids: list = download_check_enrollment_status(form)
        boar_ids: list = download_check_line(boar_ids, form)
        boars_query: flask_sqlalchemy.BaseQuery = \
            download_check_farm(boar_ids, form)
        return exporter.downloadExcel(boars_query)
    return render_template(
        './boars/download.html', user=current_user, form=form)


def download_check_enrollment_status(form: forms.BoarDownload) -> list:
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


def download_check_line(boar_ids: list, form: forms.BoarDownload) -> list:
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
    boar_list = Boar.query.filter(and_(
        Boar.id.in_(boar_ids), Boar.line.in_(lines),))
    return [x.id for x in boar_list]


def download_check_farm(
    boar_ids: list, form: forms.BoarDownload
) -> flask_sqlalchemy.BaseQuery:
    """選択した農場の雄を返す

    Args:
        boar_ids (list): 雄id(インデックス番号)
        form (BoarDownload): フォーム入力内容

    Returns:
        flask_sqlalchemy.BaseQuery: 雄一覧
    """
    farms: list = []
    if form.ggp1.data:
        farms.append(41)
    if form.ggp2.data:
        farms.append(42)
    if form.east.data:
        farms.append(61)
    return Boar.query.filter(and_(
        Boar.id.in_(boar_ids), Boar.farm_id.in_(farms),))

    # TODO: 状態モデルの作成と雄モデルの接続
    # TODO: AIセンターモデルと編集権限
