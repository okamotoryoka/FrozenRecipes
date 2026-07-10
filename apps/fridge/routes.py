from flask import Blueprint, render_template, request, redirect
from flask_login import login_required, current_user
from apps.auth.h2db import get_connection
from datetime import datetime, date
from apps.gemini.service import generate_recipe

fridge_bp = Blueprint("fridge", __name__, url_prefix="/fridge")


@fridge_bp.route("/list")
@login_required
def list_items():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
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
    """,
        (current_user.id,),
    )

    rows = cur.fetchall()
    conn.close()

    today = date.today()
    items = []

    for r in rows:

        expiry_alert = None
        best_before_alert = None

        # 消費期限
        if r[4]:
            expiry_date = datetime.strptime(str(r[4]), "%Y-%m-%d").date()

            days_left = (expiry_date - today).days

            if days_left < 0:
                expiry_alert = f"❌ 消費期限切れ ({abs(days_left)}日経過)"
            elif days_left <= 3:
                expiry_alert = f"⚠ 消費期限まであと{days_left}日"

        # 賞味期限
        if r[5]:
            best_before_date = datetime.strptime(str(r[5]), "%Y-%m-%d").date()

            days_left = (best_before_date - today).days

            if days_left < 0:
                best_before_alert = f"⚠ 賞味期限切れ ({abs(days_left)}日経過)"
            elif days_left <= 3:
                best_before_alert = f"⚠ 賞味期限まであと{days_left}日"

        items.append(
            {
                "id": r[0],
                "name": r[1],
                "quantity": r[2],
                "unit": r[3],
                "expiry_date": r[4],
                "best_before_date": r[5],
                "expiry_alert": expiry_alert,
                "best_before_alert": best_before_alert,
            }
        )

    return render_template("fridge_list.html", items=items)


@fridge_bp.route("/recipe")
@login_required
def fridge_recipe():

    try:
        conn = get_connection()
        cur = conn.cursor()

        cur.execute(
            """
            SELECT
                NAME,
                EXPIRY_DATE,
                BEST_BEFORE_DATE
            FROM FRIDGE_ITEMS
            WHERE USER_ID = ?
        """,
            (current_user.id,),
        )

        rows = cur.fetchall()
        conn.close()

        today = date.today()
        foods = []

        for row in rows:

            name = row[0]
            expiry_date = row[1]
            best_before_date = row[2]

            use_food = True

            # 消費期限チェック
            if expiry_date:
                expiry = datetime.strptime(str(expiry_date), "%Y-%m-%d").date()

                if expiry < today:
                    use_food = False

            # 賞味期限チェック
            if best_before_date:
                best_before = datetime.strptime(
                    str(best_before_date), "%Y-%m-%d"
                ).date()

                if best_before < today:
                    use_food = False

            if use_food:
                foods.append(name)

        if foods:

            recipe = generate_recipe(foods)

            # レシピ一覧へ保存
            conn = get_connection()
            cur = conn.cursor()

            title = "・".join(foods[:3]) + "の料理"

            cur.execute(
                """
                INSERT INTO RECIPES
                (
                    USER_ID,
                    TITLE,
                    RECIPE_TEXT,
                    IMAGE_PATH
                )
                VALUES (?, ?, ?, ?)
            """,
                (current_user.id, title, recipe, None),
            )

            conn.commit()
            conn.close()

        else:

            recipe = "使用できる食材がありません。"

    except Exception as e:

        print(e)

        recipe = (
            "現在レシピ生成サービスが混雑しています。"
            "時間をおいて再度お試しください。"
        )

    return render_template("fridge_recipe.html", foods=foods, recipe=recipe)


@fridge_bp.route("/delete/<int:item_id>", methods=["POST"])
@login_required
def delete_item(item_id):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        DELETE FROM FRIDGE_ITEMS
        WHERE ID = ?
        AND USER_ID = ?
    """,
        (item_id, current_user.id),
    )

    conn.commit()
    conn.close()

    return redirect("/fridge/list")


@fridge_bp.route("/add", methods=["POST"])
@login_required
def add_item():

    name = request.form["name"]
    quantity = request.form.get("quantity")
    unit = request.form.get("unit")

    best_before_date = request.form.get("best_before_date") or None
    expiry_date = request.form.get("expiry_date") or None

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
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
    """,
        (current_user.id, name, quantity, unit, expiry_date, best_before_date),
    )

    conn.commit()
    conn.close()

    return redirect("/fridge/list")
