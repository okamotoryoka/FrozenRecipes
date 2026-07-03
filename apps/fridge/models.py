from apps.app import db

class Ingredient(db.Model):

    __tablename__ = "ingredients"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    name = db.Column(
        db.String(100),
        nullable=False
    )

    expiry_date = db.Column(
        db.Date
    )

    image_path = db.Column(
        db.String(255)
    )