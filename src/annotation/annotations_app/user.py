from flask_login import UserMixin

from annotations_app.config import logging, Config
from annotations_app.models.base import User as UserModel
from annotations_app.utils import db_session
from annotations_app.flask_app import db

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

        if self.is_superuser_email(email):
            self._is_active = True
            self.is_superuser = True
        else:
            self._is_active = is_active
            self.is_superuser = is_superuser

    @staticmethod
    def is_superuser_email(email):
        if email in Config.AUTH_WHITELISTED_EMAILS:
            return True
        return False

    @property
    def is_active(self):
        # this must be property due to flask-login requirements, so have to be a bit ugly
        return self._is_active

    @staticmethod
    def get(user_id=None, provider_id=None, email=None, default_fields=None):
        """
        Provide either user_id, provider_id or email
        Return None if user is not in the database or user if it's present

        If email is provided - and it's superuser email (complex rules) - always return this user,
        create in DB if needed, filling the user with default_fields values

        If user is found and default_fields changed - update the database object (changed name, profile pic, etc)
        """
        if default_fields is None:
            default_fields = dict()

        user_from_db = db.session.query(UserModel)

        if user_id:
            user_from_db = user_from_db.filter(UserModel.id == user_id)
        elif provider_id:
            user_from_db = user_from_db.filter(
                UserModel.provider_id == provider_id
            )
        elif email:
            # logic warning: if we use multiple auth providers it might be unsafe
            user_from_db = user_from_db.filter(
                UserModel.email == email
            )
        else:
            raise Exception("Please provide a way to retrieve the user")
        user_from_db = user_from_db.first()
        if not user_from_db:
            logging.info(f"User {email,provider_id} not found in the database. Trying other options.")
            # Plan for a new user queue
            # 1. superusers always get created
            # 2. Non-superusers get stubbed out with is_active=false
            # 3. Create a new user queue that gets processed by admins
            if email and User.is_superuser_email(email):
                # special case - first login by superuser on fresh setup/database
                superuser = User.create(
                    provider_id=default_fields.get("provider_id"),
                    name=default_fields.get("name"),
                    email=default_fields.get("email"),
                    profile_pic=default_fields.get("profile_pic"),
                    is_active=True,
                    is_superuser=True
                )
                logging.info("Superuser %s (%s) first login", superuser.email, superuser.provider_id)
                return superuser
            # to stub out a user, require that they have a provider_id and email
            elif email and provider_id:
                logging.info("Stubbing out new user %s (%s)", email, provider_id)
                newuser = User.create(
                    provider_id=default_fields.get("provider_id"),
                    name=default_fields.get("name"),
                    email=default_fields.get("email"),
                    profile_pic=default_fields.get("profile_pic"),
                    is_active=False,
                    is_superuser=False
                )
                return newuser
            logging.info("No valid user found")
            return None

        # update user's data on each login
        for field, value in default_fields.items():
            if getattr(user_from_db, field, None) != value:
                setattr(user_from_db, field, value)
                logging.info("User %s field updated to %s", user_from_db, value)

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
    def create(*, provider_id, name, email, profile_pic, is_active=False, is_superuser=False):
        user = UserModel(
            provider_id=provider_id,
            name=name,
            email=email,
            profile_pic=profile_pic,
            is_active=is_active,
            is_superuser=is_superuser,
        )
        db.session.add(user)
        db.session.commit()
        db.session.refresh(user)
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
