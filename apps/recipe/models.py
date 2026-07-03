from apps.app import db

class Recipe(db.Model):

    __tablename__ = "recipes"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    title = db.Column(
        db.String(100)
    )

    content = db.Column(
        db.Text
    )