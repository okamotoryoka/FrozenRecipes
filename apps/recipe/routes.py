from flask import Blueprint, render_template, request, redirect
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
import json

from apps.gemini.service import detect_foods, generate_recipe
from apps.auth.h2db import get_connection

recipe_bp = Blueprint("recipe", __name__, url_prefix="/recipe")

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@recipe_bp.route("/generate", methods=["GET", "POST"])
@login_required
def generate():
    recipe = None
    foods = []

    if request.method == "POST":
        file = request.files.get("image")

        if file and file.filename != "":
            filename = secure_filename(file.filename)
            path = os.path.join(UPLOAD_FOLDER, filename)
            file.save(path)

            # 食材抽出
            foods = detect_foods(path)

            # レシピ生成
            recipe_text = generate_recipe(foods)

            # タイトル生成
            title = f"{foods[0] if foods else 'レシピ'}の料理"

            # DB保存
            conn = get_connection()
            cur = conn.cursor()

            cur.execute(
                """
                INSERT INTO RECIPES (USER_ID, TITLE, RECIPE_TEXT, IMAGE_PATH)
                VALUES (?, ?, ?, ?)
                """,
                (
                    current_user.id,
                    title,
                    recipe_text,
                    path
                )
            )

            conn.commit()
            conn.close()

            recipe = recipe_text

    return render_template("recipe.html", recipe=recipe, foods=foods)


@recipe_bp.route("/list")
@login_required
def list_recipes():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    SELECT ID, TITLE, RECIPE_TEXT, IMAGE_PATH
    FROM RECIPES
    WHERE USER_ID = ?

    UNION

    SELECT
        r.ID,
        r.TITLE,
        r.RECIPE_TEXT,
        r.IMAGE_PATH
    FROM BOOKMARKS b
    JOIN POSTS p ON b.POST_ID = p.ID
    JOIN RECIPES r ON p.RECIPE_ID = r.ID
    WHERE b.USER_ID = ?

    ORDER BY ID DESC
""", (current_user.id, current_user.id))

    rows = cur.fetchall()
    conn.close()

    recipes = [
        {
            "id": r[0],
            "title": r[1],
            "text": r[2],
            "image": r[3],
        }
        for r in rows
    ]

    return render_template("recipe_list.html", recipes=recipes)


# 追加する削除機能
@recipe_bp.route("/delete/<int:recipe_id>", methods=["POST"])
@login_required
def delete_recipe(recipe_id):
    conn = get_connection()
    cur = conn.cursor()

    # 画像パス取得
    cur.execute("""
        SELECT IMAGE_PATH
        FROM RECIPES
        WHERE ID = ? AND USER_ID = ?
    """, (recipe_id, current_user.id))

    row = cur.fetchone()

    if row:
        image_path = row[0]

        # 画像削除
        if image_path and os.path.exists(image_path):
            os.remove(image_path)

        # レシピ削除
        cur.execute("""
            DELETE FROM RECIPES
            WHERE ID = ? AND USER_ID = ?
        """, (recipe_id, current_user.id))

        conn.commit()

    conn.close()

    return redirect("/recipe/list")