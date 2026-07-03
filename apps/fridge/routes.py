from flask import Blueprint, render_template, request, redirect
from flask_login import login_required, current_user
from apps.auth.h2db import get_connection
from datetime import datetime, date

fridge_bp = Blueprint("fridge", __name__, url_prefix="/fridge")


@fridge_bp.route("/list")
@login_required
def list_items():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    SELECT
        ID,
        NAME,
        QUANTITY,
        UNIT,
        EXPIRY_DATE,
        BEST_BEFORE_DATE
    FROM FRIDGE_ITEMS
    WHERE USER_ID = ?
    ORDER BY EXPIRY_DATE ASC
    """, (current_user.id,))

    rows = cur.fetchall()
    conn.close()

    today = date.today()

    items = []

    for r in rows:

        expiry_alert = None
        best_before_alert = None

        # 消費期限
        if r[4]:
            expiry_date = datetime.strptime(
                str(r[4]), "%Y-%m-%d"
            ).date()

            days_left = (expiry_date - today).days

            if days_left < 0:
                expiry_alert = f"❌ 消費期限切れ ({abs(days_left)}日経過)"
            elif days_left <= 3:
                expiry_alert = f"⚠ 消費期限まであと{days_left}日"

        # 賞味期限
        if r[5]:
            best_before_date = datetime.strptime(
                str(r[5]), "%Y-%m-%d"
            ).date()

            days_left = (best_before_date - today).days

            if days_left < 0:
                best_before_alert = f"⚠ 賞味期限切れ ({abs(days_left)}日経過)"
            elif days_left <= 3:
                best_before_alert = f"⚠ 賞味期限まであと{days_left}日"

        items.append({
            "id": r[0],
            "name": r[1],
            "quantity": r[2],
            "unit": r[3],
            "expiry_date": r[4],
            "best_before_date": r[5],
            "expiry_alert": expiry_alert,
            "best_before_alert": best_before_alert
        })

    return render_template(
        "fridge_list.html",
        items=items
    )


@fridge_bp.route("/add", methods=["POST"])
@login_required
def add_item():

    name = request.form["name"]
    quantity = request.form.get("quantity")
    unit = request.form.get("unit")

    # 空文字なら None にする
    best_before_date = request.form.get("best_before_date") or None
    expiry_date = request.form.get("expiry_date") or None

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO FRIDGE_ITEMS
        (
            USER_ID,
            NAME,
            QUANTITY,
            UNIT,
            EXPIRY_DATE,
            BEST_BEFORE_DATE
        )
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        current_user.id,
        name,
        quantity,
        unit,
        expiry_date,
        best_before_date
    ))

    conn.commit()
    conn.close()

    return redirect("/fridge/list")

@fridge_bp.route("/delete/<int:item_id>", methods=["POST"])
@login_required
def delete_item(item_id):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        DELETE FROM FRIDGE_ITEMS
        WHERE ID = ?
        AND USER_ID = ?
    """, (item_id, current_user.id))

    conn.commit()
    conn.close()

    return redirect("/fridge/list")