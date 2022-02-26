import pandas as pd
from config import engine
from flask import flash
import re


from mendel_japan.models import Line


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
    df_rename = df[~(df.tattoo.isin(already_registered().tattoo))]
    if len(df_rename) > 1:
        topigs_only = add_topigs_filter(df_rename)
        boar_rename = rename_to_boar(topigs_only)
        boar_rename['farm_id'] = farm_id
        append_database(boar_rename)
    else:
        flash(f'{filename}に未登録の雄はいませんでした。', 'error')


def already_registered() -> pd.DataFrame:
    """
    boarsテーブルから登録済みの雄一覧を抽出して返す

    Returns:
        pd.DataFrame: boarsテーブルに登録済みの雄
    """
    columns = ['tattoo', 'name', 'line_id', 'birth_on']
    return pd.read_sql('boars', engine, columns=columns)


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
        'Line': '系統',
        '系統': '系統',
        'Date birth': 'birth_on',
        '生年月日': 'birth_on',
        'Date Mortality': 'culling_on',
        '淘汰日': 'culling_on'
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
    top_cell_value: str = pd.read_excel(file_path).columns.values[0]
    print('**********************')
    print(top_cell_value)
    columns = ['tattoo', 'name', '系統', 'birth_on', 'culling_on']
    if 'Applied filters' in top_cell_value:
        return pd.read_excel(file_path, header=2) \
            .rename(columns=change_columns_title()) \
            .query('tattoo == tattoo')[columns]

    elif top_cell_value == 'タトゥー':
        return pd.read_excel(file_path) \
            .rename(columns=change_columns_title())


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
    df.loc[df['系統'] == 'MMMM', 'name'] = \
        df['tattoo'].replace({'UR': '', 'EN': ''}, regex=True)

    df.loc[df['系統'] != 'MMMM', 'name'] = df.apply(
        lambda x: line_to_head(x.系統) + re.sub(r"\D", '', x.tattoo), axis=1)

    df.loc[:, 'line_id'] = df.apply(lambda x: lines(x.系統), axis=1)
    return df.drop('系統', axis=1)


def line_to_head(line: str) -> str:
    """
    トピッグスの系統から雄IDの頭につくアルファベットを返す

    Args:
        line (str): 系統

    Returns:
        str: 雄IDの頭につくアルファベット2文字
    """
    line_to_name: dict = {'LLLL': 'LL', 'NNNN': 'TL', 'ZZZZ': 'TW', 'MMMM': ''}
    return line_to_name[line]


def lines(line: str) -> int:
    """該当の系統名のidを返す

    Args:
        line (str): 系統(アルファベット4文字)

    Returns:
        int: 系統モデルのインデックス番号
    """
    return Line.query.filter(Line.line == line).first().id


def append_database(df: pd.DataFrame) -> None:
    """
    各処理が終わったデータフレームをboarsテーブルに取り込み
    取り込み完了後flashを表示

    Args:
        df (pd.DataFrame): [description]
    """
    df.to_sql('boars', engine, index=False, if_exists='append')
    flash(f'{len(df)}頭追加しました。')


def add_topigs_filter(df):
    topigs_lines = ['LLLL', 'NNNN', 'ZZZZ']
    return df[df['系統'].isin(topigs_lines)]
