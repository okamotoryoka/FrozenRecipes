from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms import PasswordField
from wtforms import SubmitField

from wtforms.validators import DataRequired
from wtforms.validators import Length


class LoginForm(FlaskForm):

    username = StringField(
        "ユーザー名",
        validators=[
            DataRequired(),
            Length(max=50)
        ]
    )

    password = PasswordField(
        "パスワード",
        validators=[
            DataRequired(),
            Length(max=100)
        ]
    )

    submit = SubmitField("ログイン")