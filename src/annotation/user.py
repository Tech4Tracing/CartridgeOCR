from flask_login import UserMixin
import sqlalchemy as sqldb 
from utils import get_db

class User(UserMixin):
    def __init__(self, id_, name, email, profile_pic):
        self.id = id_
        self.name = name
        self.email = email
        self.profile_pic = profile_pic

    @staticmethod
    def get(user_id):
        db = get_db()
        users = db.metadata.tables['user']
        query = sqldb.select([users]).where(users.columns.id == user_id)
        user = db.connection.execute(query).one_or_none()
        if user is None:
            return None

        user = User(
            id_=user['id'], name=user['name'], email=user['email'], profile_pic=user['profile_pic']
        )
        return user

    @staticmethod
    def create(id_, name, email, profile_pic):
        db = get_db()
        users = db.metadata.tables['user']
        query = sqldb.insert(users, {'id': id_, 'name': name, 'email': email, 'profile_pic': profile_pic})
        db.connection.execute(query)