"""雄モデル関連の入力フォームクラス

    ・雄情報登録及び編集用
    ・一括登録用ファイルアップロード用
    ・Excelファイルダウンロード用
    """
from flask import Flask
from mendel_japan.models import Farm, Line
from flask_wtf import FlaskForm
from wtforms import (
    StringField, DateField, validators, SubmitField, FileField, RadioField,
    BooleanField, SelectField)


class BoarForm(FlaskForm):
    """雄情報登録及び編集用クラス"""
    tattoo = StringField('タトゥー', validators=[
        validators.InputRequired('必須です'),
        validators.Length(max=10, message='10文字以内で入力してください')])
    name = StringField('雄ID', validators=[
        validators.InputRequired('必須です'),
        validators.Length(max=10, message='10文字以内で入力してください')])
    birth_on = DateField('生年月日', validators=[
        validators.Optional(strip_whitespace=True)])
    culling_on = DateField('淘汰日', validators=[
        validators.Optional(strip_whitespace=True)])
    farm_id = SelectField('農場', coerce=int)
    line_id = SelectField('系統', coerce=int)
    submit = SubmitField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._set_farms()
        self._set_lines()

    def _set_farms(self) -> None:
        """Farmモデルのデータを選択肢として表示させる

        Args:
            self (BoarForm): 入力フォーム
        """
        farms: Farm = Farm.query.order_by(Farm.id).all()
        self.farm_id.choices = [(farm.id, farm.name) for farm in farms]

    def _set_lines(self) -> None:
        """Lineモデルのデータを選択肢として表示させる

        Args:
            self (BoarForm): 入力フォーム
        """
        lines: Line = Line.query.order_by(Line.code).all()
        self.line_id.choices = \
            [(line.id, f'{line.code} ({line.name})') for line in lines]


class BoarUpload(FlaskForm):
    """雄リスト一括登録用クラス"""
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
        farms: Farm = Farm.query.order_by(Farm.id).all()
        self.farm_id.choices = [(farm.id, farm.name) for farm in farms]


class BoarDownload(FlaskForm):
    """雄リストダウンロード用クラス"""
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

    ggp1_farm = BooleanField('GGP')
    ggp2_farm = BooleanField('第2農場')
    east_farm = BooleanField('東日本')
    submit = SubmitField()


class StatusForm(FlaskForm):
    """状態登録用クラス"""
    start_on = DateField(
        '日付', validators=[validators.InputRequired('必須です')])
    status = SelectField('状態', choices=[
        ('生産可', '生産可'), ('生産外', '生産外'), ('注意', '注意')
    ])
    reason = StringField('理由', validators=[
        validators.Length(max=10, message='10文字以内で入力してください')])
    submit = SubmitField()
