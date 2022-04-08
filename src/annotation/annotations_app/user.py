from flask_login import UserMixin

from annotations_app.models.base import User as UserModel
from annotations_app.utils import db_session


class User(UserMixin):

    def __init__(self, *, id, provider_id, name, email, profile_pic, is_active, is_superuser):
        """
        Note: we have UserModel object which is handy to work with database but use our custom
        User object from this file because flask_login needs it as is; proxying and copying data
        between them. If this approach proves uncomfortable or you know how to do better please do

        ID example: uuid
        provider_id example: google56788437437473743743 or azure483843 or whatever
        """
        self.id = id
        self.provider_id = provider_id
        self.name = name
        self.email = email
        self.profile_pic = profile_pic

        # ugly but useful hardcode, which we might move to env variables
        # or just assume that all users are inactive and non-superuser from beginning and update the DB manually
        if email.endswith("@gosource.com.au") or email == "robert.sim@gmail.com":
            self._is_active = True
            self.is_superuser = True
        else:
            self._is_active = is_active
            self.is_superuser = is_superuser

    @property
    def is_active(self):
        return self._is_active

    @staticmethod
    def get(user_id=None, provider_id=None):
        with db_session() as db:
            user_from_db = db.query(UserModel)

            if user_id:
                user_from_db = user_from_db.filter(UserModel.id == user_id)
            elif provider_id:
                user_from_db = user_from_db.filter(
                    UserModel.provider_id == provider_id)
            else:
                raise Exception("Please provide either user_id or provider_id")
            user_from_db = user_from_db.first()
            if not user_from_db:
                return None
            return User(
                id=user_from_db.id,
                provider_id=user_from_db.provider_id,
                name=user_from_db.name,
                email=user_from_db.email,
                profile_pic=user_from_db.profile_pic,
                is_active=user_from_db.is_active,
                is_superuser=user_from_db.is_superuser,
            )

    @staticmethod
    def create(*, provider_id, name, email, profile_pic):
        with db_session() as db:
            user = UserModel(
                provider_id=provider_id,
                name=name,
                email=email,
                profile_pic=profile_pic,
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            return User(
                id=user.id,
                provider_id=user.provider_id,
                name=user.name,
                email=user.email,
                profile_pic=user.profile_pic,
                is_active=user.is_active,
                is_superuser=user.is_superuser,
            )

    def __str__(self):
        return f"User {self.email}"
