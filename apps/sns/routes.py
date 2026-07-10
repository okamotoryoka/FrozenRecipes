from flask import render_template, request, redirect, url_for, current_app
from flask_login import login_required, current_user

from apps.auth.h2db import get_connection
from apps.sns import sns_bp


# -------------------------
# タイムライン
# -------------------------
@sns_bp.route("/")
@login_required
def timeline():

    conn = get_connection()
    cur = conn.cursor()

    # 投稿
    cur.execute("""
SELECT
    p.ID,
    p.USER_ID,
    u.USERNAME,
    p.IMAGE_PATH,
    p.CAPTION,
    COUNT(DISTINCT l.ID) AS LIKE_COUNT,
    CASE
        WHEN COUNT(DISTINCT my_like.ID) > 0 THEN 1
        ELSE 0
    END AS IS_LIKED
FROM POSTS p
JOIN USERS u ON p.USER_ID = u.ID
LEFT JOIN LIKES l ON p.ID = l.POST_ID
LEFT JOIN LIKES my_like
    ON p.ID = my_like.POST_ID
   AND my_like.USER_ID = ?
GROUP BY
    p.ID, p.USER_ID, u.USERNAME, p.IMAGE_PATH, p.CAPTION
ORDER BY p.CREATED_AT DESC
""", (current_user.id,))

    posts = cur.fetchall()

    # コメント（親のみ）
    cur.execute("""
SELECT
    c.ID,
    c.POST_ID,
    c.USER_ID,
    u.USERNAME,
    c.CONTENT,
    c.PARENT_ID
FROM COMMENTS c
JOIN USERS u ON c.USER_ID = u.ID
ORDER BY c.CREATED_AT ASC
""")

    comments = cur.fetchall()

    conn.close()

    return render_template(
        "sns/sns.html",
        posts=posts,
        comments=comments
    )

# -------------------------
# 投稿作成
# -------------------------
@sns_bp.route("/post/create", methods=["GET", "POST"])
@login_required
def create_post():

    if request.method == "POST":

        try:
            import os

            caption = request.form.get("caption")

            image = request.files.get("image")

            image_path = None  # ←重要

            if image and image.filename:

                upload_folder = os.path.join(current_app.static_folder, "uploads")
                os.makedirs(upload_folder, exist_ok=True)

                filename = image.filename
                save_path = os.path.join(upload_folder, filename)

                image.save(save_path)

                image_path = "uploads/" + filename

            # ★ここ追加（安全化）
            if image_path is None:
                image_path = ""

            conn = get_connection()
            cur = conn.cursor()

            cur.execute("""
                INSERT INTO POSTS
                (USER_ID, CAPTION, IMAGE_PATH)
                VALUES (?, ?, ?)
            """, (
                current_user.id,
                caption,
                image_path
            ))

            conn.commit()
            conn.close()

        except Exception as e:
            print("❌ INSERT失敗:", repr(e))

        return redirect(url_for("sns.timeline"))

    return render_template("sns/create_post.html")


# -------------------------
# いいね
# -------------------------
@sns_bp.route("/like/<int:post_id>")
@login_required
def like(post_id):

    conn = get_connection()
    cur = conn.cursor()

    # すでにいいねしているか確認
    cur.execute("""
        SELECT ID
        FROM LIKES
        WHERE USER_ID = ? AND POST_ID = ?
    """, (current_user.id, post_id))

    like = cur.fetchone()

    if like:
        # いいね済みなら取り消し
        cur.execute("""
            DELETE FROM LIKES
            WHERE USER_ID = ? AND POST_ID = ?
        """, (current_user.id, post_id))
    else:
        # まだなら追加
        cur.execute("""
            INSERT INTO LIKES (USER_ID, POST_ID)
            VALUES (?, ?)
        """, (current_user.id, post_id))

    conn.commit()
    conn.close()

    return redirect(url_for("sns.timeline"))


# -------------------------
# コメント
# -------------------------
@sns_bp.route("/comment/<int:post_id>", methods=["POST"])
@login_required
def comment(post_id):

    content = request.form.get("content")

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO COMMENTS
        (USER_ID, POST_ID, CONTENT)
        VALUES (?, ?, ?)
    """, (
        current_user.id,
        post_id,
        content
    ))

    conn.commit()
    conn.close()

    return redirect(url_for("sns.timeline"))


# -------------------------
# ブックマーク
# -------------------------
@sns_bp.route("/bookmarks")
@login_required
def bookmarks():

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            p.ID,
            u.USERNAME,
            p.IMAGE_PATH,
            p.CAPTION,
            COUNT(l.ID) AS LIKE_COUNT
        FROM BOOKMARKS b
        JOIN POSTS p ON b.POST_ID = p.ID
        JOIN USERS u ON p.USER_ID = u.ID
        LEFT JOIN LIKES l ON p.ID = l.POST_ID
        WHERE b.USER_ID = ?
        GROUP BY p.ID
        ORDER BY p.ID DESC
    """, (current_user.id,))

    posts = cur.fetchall()
    conn.close()

    return render_template("sns/bookmarks.html", posts=posts)

@sns_bp.route("/delete/<int:post_id>", methods=["POST"])
@login_required
def delete_post(post_id):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT IMAGE_PATH
        FROM POSTS
        WHERE ID = ? AND USER_ID = ?
    """, (post_id, current_user.id))

    row = cur.fetchone()

    if not row:
        conn.close()
        return redirect(url_for("sns.timeline"))

    image_path = row[0]

    import os

    if image_path:
        file_path = os.path.join(current_app.static_folder, image_path)
        if os.path.exists(file_path):
            os.remove(file_path)

    # 関連データ削除
    cur.execute("DELETE FROM LIKES WHERE POST_ID = ?", (post_id,))
    cur.execute("DELETE FROM COMMENTS WHERE POST_ID = ?", (post_id,))
    cur.execute("DELETE FROM BOOKMARKS WHERE POST_ID = ?", (post_id,))

    # 投稿削除
    cur.execute("""
        DELETE FROM POSTS
        WHERE ID = ? AND USER_ID = ?
    """, (post_id, current_user.id))

    conn.commit()
    conn.close()

    return redirect(url_for("sns.timeline"))

@sns_bp.route("/bookmark/delete/<int:post_id>", methods=["POST"])
@login_required
def delete_bookmark(post_id):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        DELETE FROM BOOKMARKS
        WHERE USER_ID = ? AND POST_ID = ?
    """, (current_user.id, post_id))

    conn.commit()
    conn.close()

    return redirect(url_for("sns.bookmarks"))

@sns_bp.route("/bookmark/<int:post_id>")
@login_required
def bookmark(post_id):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT COUNT(*)
        FROM BOOKMARKS
        WHERE USER_ID = ? AND POST_ID = ?
    """, (current_user.id, post_id))

    if cur.fetchone()[0] == 0:
        cur.execute("""
            INSERT INTO BOOKMARKS (USER_ID, POST_ID)
            VALUES (?, ?)
        """, (current_user.id, post_id))
        conn.commit()

    conn.close()

    return redirect(url_for("sns.timeline"))


@sns_bp.route("/reply/<int:comment_id>", methods=["POST"])
@login_required
def reply(comment_id):

    content = request.form.get("content")

    conn = get_connection()
    cur = conn.cursor()

    # 親コメントからPOST_ID取得
    cur.execute("""
        SELECT POST_ID
        FROM COMMENTS
        WHERE ID = ?
    """, (comment_id,))

    row = cur.fetchone()

    if not row:
        conn.close()
        return redirect(url_for("sns.timeline"))

    post_id = row[0]

    # 返信INSERT
    cur.execute("""
        INSERT INTO COMMENTS
        (USER_ID, POST_ID, PARENT_ID, CONTENT)
        VALUES (?, ?, ?, ?)
    """, (
        current_user.id,
        post_id,
        comment_id,
        content
    ))

    conn.commit()
    conn.close()

    return redirect(url_for("sns.timeline"))

@sns_bp.route("/comment/delete/<int:comment_id>", methods=["POST"])
@login_required
def delete_comment(comment_id):

    conn = get_connection()
    cur = conn.cursor()

    # 自分のコメントか確認
    cur.execute("""
        SELECT ID
        FROM COMMENTS
        WHERE ID = ? AND USER_ID = ?
    """, (comment_id, current_user.id))

    row = cur.fetchone()

    if not row:
        conn.close()
        return redirect(url_for("sns.timeline"))

    # 削除
    cur.execute("""
        DELETE FROM COMMENTS
        WHERE ID = ? AND USER_ID = ?
    """, (comment_id, current_user.id))

    conn.commit()
    conn.close()

    return redirect(url_for("sns.timeline"))
