from flask import Blueprint, render_template, request
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

            # ① 食材抽出
            foods = detect_foods(path)

            # ② レシピ生成
            recipe_text = generate_recipe(foods)

            # ③ タイトル生成
            title = f"{foods[0] if foods else 'レシピ'}の料理"

            # ④ 保存
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
        ORDER BY ID DESC
    """, (current_user.id,))

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