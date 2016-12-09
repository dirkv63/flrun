from . import db, lm
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash


class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(10), index=True, unique=True)
    passwork_hash = db.Column(db.String(64))

    def set_password(self, password):
        self.passwork_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.passwork_hash, password)

    @staticmethod
    def register(username, password):
        user = User()
        user.username = username
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

    def __repr__(self):
        return "<User: {user}>".format(user=self.username)

@lm.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
