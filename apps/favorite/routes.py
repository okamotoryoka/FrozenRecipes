from flask import Blueprint, redirect, render_template
from flask_login import login_required, current_user
from apps.auth.h2db import get_connection

favorite_bp = Blueprint("favorite", __name__, url_prefix="/favorite")


@favorite_bp.route("/delete/<int:recipe_id>", methods=["POST"])
@login_required
def delete_favorite(recipe_id):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        DELETE FROM FAVORITES
        WHERE USER_ID = ?
        AND RECIPE_ID = ?
    """, (
        current_user.id,
        recipe_id
    ))

    conn.commit()
    conn.close()

    return redirect("/favorite/list")


@favorite_bp.route("/list")
@login_required
def list_favorites():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT R.ID, R.TITLE, R.RECIPE_TEXT
        FROM RECIPES R
        JOIN FAVORITES F ON R.ID = F.RECIPE_ID
        WHERE F.USER_ID = ?
    """, (current_user.id,))

    rows = cur.fetchall()
    conn.close()

    favorites = [
        {
            "id": r[0],
            "title": r[1],
            "text": r[2],
        }
        for r in rows
    ]

    return render_template("favorite_list.html", favorites=favorites)