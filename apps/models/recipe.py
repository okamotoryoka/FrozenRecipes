import os
import json
from datetime import datetime

from flask import Blueprint, render_template, request
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from apps.app import db
from apps.gemini.service import detect_foods, generate_recipe

recipe_bp = Blueprint("recipe", __name__, url_prefix="/recipe")

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# =========================
# Model
# =========================
class Recipe(db.Model):
    __tablename__ = "recipes"

    id = db.Column(db.Integer, primary_key=True)
    foods = db.Column(db.Text, nullable=False)      # JSON文字列
    content = db.Column(db.Text, nullable=False)    # レシピ本文
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# =========================
# Generate
# =========================
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

            print("保存パス:", path)

            # ① 食材抽出
            foods = detect_foods(path)
            print("foods:", foods)

            # ② レシピ生成
            recipe_text = generate_recipe(foods)
            print("recipe:", recipe_text)

            # ③ DB保存（SQLAlchemy）
            recipe_obj = Recipe(
                foods=json.dumps(foods, ensure_ascii=False),
                content=recipe_text
            )

            db.session.add(recipe_obj)
            db.session.commit()

            recipe = recipe_text

    return render_template("recipe.html", recipe=recipe, foods=foods)