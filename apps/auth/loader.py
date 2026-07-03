from flask_login import UserMixin

class LoginUser(UserMixin):
    def __init__(self, user_id, username):
        self.id = user_id
        self.username = username