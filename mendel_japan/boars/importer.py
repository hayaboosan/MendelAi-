import pandas as pd
from sqlalchemy import create_engine
from config import DATABASE_URI
from flask import flash
import re


def import_boar_list(file_path: str, filename: str, farm_id: int) -> None:
    """
    アップロードしたExcelファイルのフォーマットをチェック
    データフレームに取り込みDB保存済みの雄との差を抽出(未登録の雄を抽出)
    未登録のオスがいる場合、雄IDを再作成してboarsテーブルに取り込む
    いない場合flashを表示

    Args:
        file_path (str): アップロードファイルのパス
        filename (str): アップロードファイルのファイル名
    """
    df: pd.DataFrame = check_format(file_path)
    boar_to_register: pd.DataFrame = df[
        ~(df.tattoo.isin(already_registered().tattoo))]
    if len(boar_to_register) > 1:
        boar_rename = rename_to_boar(boar_to_register)
        boar_add_farm = boar_rename.copy()
        boar_add_farm['farm_id'] = farm_id
        append_database(boar_add_farm)
    else:
        flash(f'{filename}に未登録の雄はいませんでした。', 'error')


def already_registered() -> pd.DataFrame:
    """
    boarsテーブルから登録済みの雄一覧を抽出して返す

    Returns:
        pd.DataFrame: boarsテーブルに登録済みの雄
    """
    engine = create_engine(DATABASE_URI, echo=True)
    return pd.read_sql('boars', engine, columns=columns())


def columns() -> list:
    return ['tattoo', 'name', 'line', 'birth_on']


def change_columns_title() -> dict:
    """
    アップロードしたファイルとboarsテーブルのカラム名

    Returns:
        dict: 変更前後のcolumn名
    """
    return {
        'Tattoo Number': 'tattoo',
        'タトゥー': 'tattoo',
        'Name': 'name',
        '雄ID': 'name',
        'Line': 'line',
        '系統': 'line',
        'Date birth': 'birth_on',
        '生年月日': 'birth_on',
    }


def check_format(file_path: str) -> pd.DataFrame:
    """
    アップロードファイルから雄情報を取り出し
    ブリーディングWebのファイルは2行目にタイトルなので調整
    columnタイトルをテーブルにあわせて返す

    Args:
        file_path (str): アップロードファイルのパス

    Returns:
        pd.DataFrame: アップロードファイルから取り出した雄
    """
    check: pd.DataFrame = pd.read_excel(file_path)
    column1: str = check.columns.values[0]
    if column1 == 'Applied filters: ':
        df: pd.DataFrame = pd.read_excel(file_path, header=2)
        df2 = df.rename(columns=change_columns_title())
        return df2.query('tattoo == tattoo')[columns()]
    elif column1 == 'タトゥー':
        df: pd.DataFrame = pd.read_excel(file_path)
        return df.rename(columns=change_columns_title())


def rename_to_boar(df: pd.DataFrame) -> pd.DataFrame:
    """
    DB取り込み予定の雄の雄IDを変更
    デュロック: タトゥーのアルファベット2文字を削除
    トピッグス: タトゥー数字の前に系統ごとのアルファベット2文字をつける

    Args:
        df (pd.DataFrame): DB取り込み予定の雄

    Returns:
        pd.DataFrame: 雄IDを変更した雄
    """
    df.loc[df['line'] == 'MMMM', 'name'] = \
        df['tattoo'].replace({'UR': '', 'EN': ''}, regex=True)
    df.loc[df['line'] != 'MMMM', 'name'] = df.apply(
        lambda x: lines(x.line) + re.sub(r"\D", '', x.tattoo), axis=1)
    return df


def lines(line: str) -> str:
    """
    トピッグスの系統から雄IDの頭につくアルファベットを返す

    Args:
        line (str): 系統

    Returns:
        str: 雄IDの頭につくアルファベット2文字
    """
    line_to_name: dict = {'LLLL': 'LL', 'NNNN': 'TL', 'ZZZZ': 'TW', 'MMMM': ''}
    return line_to_name[line]


def append_database(df: pd.DataFrame) -> None:
    """
    各処理が終わったデータフレームをboarsテーブルに取り込み
    取り込み完了後flashを表示

    Args:
        df (pd.DataFrame): [description]
    """
    engine = create_engine(DATABASE_URI, echo=True)
    df.to_sql('boars', engine, index=False, if_exists='append')
    flash(f'{len(df)}頭追加しました。')
