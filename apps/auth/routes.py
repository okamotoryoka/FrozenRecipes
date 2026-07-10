from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_user, logout_user, login_required

from apps.auth.forms import LoginForm
from apps.auth.h2db import get_connection
from apps.auth.login_user import LoginUser

# Blueprintを先に作成
auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


# ログイン
@auth_bp.route("/login", methods=["GET", "POST"])
def login():

    form = LoginForm()

    if form.validate_on_submit():

        conn = get_connection()
        cur = conn.cursor()

        cur.execute(
            "SELECT ID, USERNAME, PASSWORD_HASH FROM USERS WHERE USERNAME = ?",
            (form.username.data,)
        )

        row = cur.fetchone()
        conn.close()

        if row:
            user_id, username, password = row

            if password == form.password.data:
                user = LoginUser(user_id, username)
                login_user(user)
                return redirect(url_for("main.home"))

    return render_template("login.html", form=form)


# ログアウト
@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))