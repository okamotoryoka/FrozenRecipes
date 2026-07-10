from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_user, logout_user, login_required

from apps.auth.forms import LoginForm, RegisterForm
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
            (form.username.data,),
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


# 新規登録
@auth_bp.route("/register", methods=["GET", "POST"])
def register():

    form = RegisterForm()

    if form.validate_on_submit():

        conn = get_connection()
        cur = conn.cursor()

        # ユーザー名が既にあるか確認
        cur.execute("SELECT ID FROM USERS WHERE USERNAME = ?", (form.username.data,))

        if cur.fetchone():
            conn.close()
            return render_template(
                "register.html", form=form, error="このユーザー名は既に使われています。"
            )

        # 新規登録
        cur.execute(
            "INSERT INTO USERS (USERNAME, PASSWORD_HASH) VALUES (?, ?)",
            (form.username.data, form.password.data),
        )

        conn.commit()

        # 登録したユーザーを取得
        cur.execute(
            "SELECT ID, USERNAME FROM USERS WHERE USERNAME = ?", (form.username.data,)
        )

        row = cur.fetchone()
        conn.close()

        # 自動ログイン
        user = LoginUser(row[0], row[1])
        login_user(user)

        # ホームへ
        return redirect(url_for("main.home"))

    return render_template("register.html", form=form)


# ログアウト
@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))
