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
from mendel_japan.models import Boar, Farm, Line, Status
from mendel_japan.boars import exporter, forms, importer


boars = Blueprint('boars', __name__,)
js = Bundle('javascript/boars.js', output='javascript/main.js')
assets = Environment(app)
assets.register('main_js', js)

FileObject = TypeVar('FileObject')


@boars.route('/')
# @login_required
def index() -> str:
    """登録済みの雄一覧を表示

    ・ログイン中のユーザーが所属しているAIセンター管轄の農場をリストに格納
    ・農場リストを農場IDリストに変換
    ・管轄農場に所属している雄を全て取得
    ・雄一覧ページを表示

    Returns:
        str: html
    """
    boars = Boar.query.all()
    return render_template(
        './boars/index.html', user=current_user, boars=boars)


@boars.route('/create', methods=['GET', 'POST'])
# @login_required
def create() -> str:
    """新規雄情報を作成

    ・POST
        ・既存のタトゥーでないか確認
        ・未登録であれば新規雄情報を登録
        ・雄一覧ページへリダイレクト
    ・GET
        ・雄情報作成ページを表示

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


@boars.route('/<int:id>/edit', methods=['GET', 'POST'])
# @login_required
def edit(id: int) -> str:
    """既存の雄情報を編集する

    ・POST
        ・タトゥーの重複を確認
        ・問題なければ変更を登録
        ・雄一覧ページへリダイレクト
        ・重複が確認された場合、フラッシュを表示して編集ページを維持
    ・GET
        ・雄情報編集ページを表示

    Args:
        id (int): 対象の雄モデルID

    Returns:
        str: html
    """
    boar: Boar = Boar.query.get(id)
    form: forms.BoarForm = forms.BoarForm(obj=boar)
    if form.validate_on_submit():
        registered_boar: Boar = \
            Boar.query.filter_by(tattoo=form.tattoo.data).first()

        # 同じタトゥーで登録されている雄が自分自身
        # もしくは、同じタトゥーで登録されている雄がいない場合
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
    """雄モデルに登録する

    ・IDが登録済みの場合は更新
    ・IDが登録されていない場合は新規登録

    Args:
        form (BoarForm): ユーザーがフォームに入力した内容
        id (int, optional): 雄モデルID. Defaults to None.
    """
    boar: Boar = Boar.query.get(id) if id else Boar()
    boar.tattoo = form.tattoo.data
    boar.name = form.name.data
    boar.line_id = form.line_id.data
    boar.birth_on = form.birth_on.data
    boar.culling_on = form.culling_on.data
    boar.farm_id = form.farm_id.data
    if id is None:
        db.session.add(boar)
    db.session.commit()


@boars.route('/upload', methods=['GET', 'POST'])
# @login_required
def upload() -> str:
    """Excelファイルをアップロードして雄モデルを一括登録

    ・POST
        ・ファイルの拡張子を確認
        ・問題なければ一時保存し雄モデルに登録
        ・雄一覧ページへリダイレクト
        ・対象外の拡張子の場合、フラッシュを表示
    ・GET
        ・ファイルアップロードページを表示

    Returns:
        str: html
    """
    form: forms.BoarUpload = forms.BoarUpload()
    if form.validate_on_submit():
        file: request = request.files['file']

        if allowed_file(file.filename):
            save_and_import(file, form.farm_id.data)
            return redirect(url_for('boars.index'))
        else:
            flash(
                f'アップロードできるファイル形式は{ALLOWED_EXTENSIONS}です',
                'error')
    return render_template('./boars/upload.html', user=current_user, form=form)


def allowed_file(filename: str) -> bool:
    """アップロードファイルの拡張子をチェック

    ・ファイル名の最右のドットの右側を抽出
    ・ファイル名にドットがあり、指定の拡張子の場合Trueを返す

    Args:
        filename (str): アップロードファイル名

    Returns:
        bool: ファイル名にドットがあり、指定の拡張子であるか
    """
    extension: str = filename.rsplit('.', 1)[-1].lower()
    return '.' in filename and extension in ALLOWED_EXTENSIONS


def save_and_import(file: FileObject, farm_id: int) -> None:
    """アップロードファイルの内容を

    ・アップロードしたファイルをtmpディレクトリに一時保管
    ・ファイル内容を雄モデルに登録

    Args:
        file (FileObject): アップロードファイル
        farm_id (int): 雄モデルを登録する農場のID
    """
    filename: str = secure_filename(file.filename)
    file_path: str = os.path.join(UPLOAD_FOLDER, filename)
    file.save(file_path)
    importer.import_boar_list(file_path, filename, farm_id)


@boars.route('/delete-boar', methods=['POST'])
# @login_required
def delete_boar() -> jsonify:
    """雄モデルを削除する

    ・boars.jsからデータを取得
    ・抽出した雄モデルIDの雄を削除
    ・削除処理完了後boars.jsにて表示中の一覧から削除

    Returns:
        jsonify: 空のJSON
    """
    data: dict = json.loads(request.data)
    boar: Boar = Boar.query.get(data['boarId'])
    if boar:
        db.session.delete(boar)
        db.session.commit()
    return jsonify({})


@boars.route('/download', methods=['GET', 'POST'])
# @login_required
def download() -> str | wrappers.Response:
    """雄一覧のExcelファイルをダウンロード

    ・POST
        ・選択した在籍状況の雄を抽出
        ・選択した系統で絞り込み
        ・さらに選択した農場で絞り込み
        ・雄一覧をExcelファイルにエクスポート
        ・Excelファイルをダウンロード
    ・GET
        ・雄一覧ダウンロードページを表示

    Returns:
        str: HTML | flask.wrappers.Response: レスポンス(Excelファイル)
    """
    form: forms.BoarDownload = forms.BoarDownload()
    if form.validate_on_submit():
        # 在籍状況
        boar_enrollment_status_ids: list = \
            download_check_enrollment_status(form)
        # 系統
        boar_line_ids: list = \
            download_check_line(boar_enrollment_status_ids, form)
        # 農場
        boars_query: flask_sqlalchemy.BaseQuery = \
            download_check_farm(boar_line_ids, form)
        return exporter.downloadExcel(boars_query)
    return render_template(
        './boars/download.html', user=current_user, form=form)


def download_check_enrollment_status(form: forms.BoarDownload) -> list:
    """選択した在籍状況の雄モデルIDをリストで返す

    Args:
        form (BoarDownload): フォーム入力内容

    Returns:
        list: 雄モデルID
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
    """選択した系統の雄モデルIDをリストで返す

    Args:
        boar_ids (list): 雄モデルID
        form (BoarDownload): フォーム入力内容

    Returns:
        list: 雄モデルID
    """
    lines: list = []
    for line in form:
        if 'line' in line.id and line.data:
            lines.append(Line.query.filter(
                Line.abbreviation == line.label.text).first().id)

    boar_list = Boar.query.filter(and_(
        Boar.id.in_(boar_ids), Boar.line_id.in_(lines),))
    return [x.id for x in boar_list]


def download_check_farm(
    boar_ids: list, form: forms.BoarDownload
) -> flask_sqlalchemy.BaseQuery:
    """選択した農場の雄モデルIDをリストで返す

    Args:
        boar_ids (list): 雄モデルID
        form (BoarDownload): フォーム入力内容

    Returns:
        flask_sqlalchemy.BaseQuery: 雄一覧
    """
    farms: list = []
    for farm in form:
        if 'farm' in farm.id and farm.data:
            farms.append(Farm.query.filter(
                Farm.abbreviation == farm.label.text).first().id)

    return Boar.query.filter(and_(
        Boar.id.in_(boar_ids), Boar.farm_id.in_(farms),))


@boars.route('/<int:id>', methods=['GET', 'POST'])
# @login_required
def show(id: int) -> str:
    boar: Boar = Boar.query.get(id)
    form: forms.StatusForm = forms.StatusForm()
    if form.validate_on_submit():
        status = Status()
        status.boar_id = boar.id
        status.status = form.status.data
        status.reason = form.reason.data
        status.start_on = form.start_on.data
        db.session.add(status)
        db.session.commit()
        flash('状態を登録しました', category='success')
        return redirect(url_for('boars.show', id=boar.id))
    else:
        return render_template(
            './boars/show.html', user=current_user, boar=boar, form=form)


@boars.route('/status/<int:id>/edit', methods=['GET', 'POST'])
# @login_required
def status_edit(id: int) -> str:
    status: Status = Status.query.get(id)
    form: forms.StatusForm = forms.StatusForm(obj=status)
    if form.validate_on_submit():
        status = Status.query.get(id)
        status.status = form.status.data
        status.reason = form.reason.data
        status.start_on = form.start_on.data
        db.session.commit()
        flash('状態を更新しました', category='success')
        return redirect(url_for('boars.show', id=status.boar_id))
    else:
        return render_template(
            './boars/status_edit.html', user=current_user, form=form,
            status=status)


@boars.route('/status/<int:id>/delete')
def status_delete(id: int):
    status = Status.query.get(id)
    db.session.delete(status)
    db.session.commit()
    flash('状態を削除しました', category='error')
    return redirect(url_for('boars.show', id=status.boar_id))
