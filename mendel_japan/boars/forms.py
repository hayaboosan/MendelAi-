from mendel_japan.models import Farm
from flask_wtf import FlaskForm
from wtforms import (
    StringField, DateField, validators, SubmitField, FileField, RadioField,
    BooleanField, SelectField)
from sqlalchemy import asc


class BoarForm(FlaskForm):
    """雄情報登録及び編集用クラス"""
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

    def _set_farms(self) -> None:
        """Farmモデルのデータを選択肢として表示させる

        Args:
            self (BoarForm): 入力フォーム
        """
        farms: Farm = Farm.query.order_by(asc(Farm.id)).all()
        self.farm_id.choices = [(farm.id, farm.name) for farm in farms]


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
        farms: Farm = Farm.query.order_by(asc(Farm.id)).all()
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

    ggp1 = BooleanField('GGP')
    ggp2 = BooleanField('第2農場')
    east = BooleanField('東日本')
    submit = SubmitField()
