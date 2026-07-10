from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length


class LoginForm(FlaskForm):
    username = StringField("ユーザー名", validators=[DataRequired()])

    password = PasswordField("パスワード", validators=[DataRequired()])

    submit = SubmitField("ログイン")


class RegisterForm(FlaskForm):
    username = StringField(
        "ユーザー名", validators=[DataRequired(), Length(min=1, max=20)]
    )

    password = PasswordField("パスワード", validators=[DataRequired(), Length(min=4)])

    submit = SubmitField("新規登録")
