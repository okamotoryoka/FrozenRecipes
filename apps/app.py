from flask import Flask
from flask_login import LoginManager
import os

from apps.auth.h2db import get_connection
from apps.auth.login_user import LoginUser

login_manager = LoginManager()
login_manager.login_view = "auth.login"


def create_app():

    app = Flask(
        __name__,
        static_folder=os.path.join(
            os.path.dirname(__file__),
            "static"
        )
    )

    print("STATIC_FOLDER =", app.static_folder)

    app.config["SECRET_KEY"] = "secret"

    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        conn = get_connection()
        cur = conn.cursor()

        cur.execute(
            "SELECT ID, USERNAME FROM USERS WHERE ID = ?",
            (user_id,)
        )

        row = cur.fetchone()
        conn.close()

        if row:
            return LoginUser(row[0], row[1])

        return None

    from apps.auth.routes import auth_bp
    from apps.recipe.routes import recipe_bp
    from apps.fridge.routes import fridge_bp
    from apps.favorite.routes import favorite_bp
    from apps.main.routes import main_bp
    from apps.sns.routes import sns_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(recipe_bp)
    app.register_blueprint(fridge_bp)
    app.register_blueprint(favorite_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(sns_bp)

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)