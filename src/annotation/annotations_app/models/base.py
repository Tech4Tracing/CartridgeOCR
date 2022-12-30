import datetime
import random
import uuid

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy_mixins import AllFeaturesMixin
from sqlalchemy import Boolean, ForeignKey, Integer, Text, String, DateTime, Float
from sqlalchemy.orm import relationship
from sqlalchemy import and_, or_

db = SQLAlchemy()


class BaseModel(db.Model, AllFeaturesMixin):
    __abstract__ = True
    pass


BaseModel.set_session(db.session)


class Annotation(BaseModel):
    __tablename__ = 'annotations'

    id = db.Column(String(36), primary_key=True, default=uuid.uuid4)
    created_at = db.Column(DateTime(timezone=True), default=datetime.datetime.utcnow)

    image_id = db.Column(String(36), ForeignKey("images.id"))
    image = relationship("Image", back_populates="annotations")
    geometry = db.Column(Text)
    annotation = db.Column(Text)
    prediction_id = db.Column(String(36), nullable=True) #, ForeignKey("predictions.id"), nullable=True)
    metadata_ = db.Column('metadata', Text)

    def __str__(self):
        return self.id


# TODO: deprecate
class Global(db.Model):
    __tablename__ = 'globals'

    key = db.Column(String(8000), primary_key=True)
    value = db.Column(Text)


class User(BaseModel):
    __tablename__ = 'users'

    # ID in our system
    id = db.Column(String(36), primary_key=True, default=uuid.uuid4)

    # for 3rd party identity providers credentials
    # something like google56789098767890 or awsiam4377437437
    provider_id = db.Column(String(255), default=None, nullable=True)

    # normal user info
    name = db.Column(String(255), nullable=False, default="")
    email = db.Column(String(255), nullable=False)
    profile_pic = db.Column(String(2048), nullable=False, default="")
    is_active = db.Column(Boolean, default=True, nullable=False)
    is_superuser = db.Column(Boolean, default=False, nullable=False)

    @staticmethod
    def get_user_by_email(email):
        return db.session.query(User).filter(User.email == email).first()
    
    @staticmethod
    def get_user_by_id(id):
        return db.session.query(User).filter(User.id == id).first()


def generate_short_id(len: int = 15):
    """
    Generates short random value, useful for unique IDs but shorter and more readable than UUID
    """
    return "".join(
        random.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")
        for i in range(0, len)
    )


class ImageCollection(BaseModel):
    __tablename__ = 'imagecollections'

    id = db.Column(String(36), primary_key=True, default=generate_short_id)
    created_at = db.Column(DateTime(timezone=True), default=datetime.datetime.utcnow)

    user_id = db.Column(String(255))
    name = db.Column(String(255))
    guest_users = db.column(Text) # comma-separated list of (user id, write-access) tuples

    images = relationship("Image", back_populates="collection")

    def __str__(self):
        return self.id

    @property
    def images_count(self):
        return db.session.query(Image).filter(
            Image.collection_id == self.id,
        ).count()

    @property
    def annotations_count(self):
        try:
            image_ids = Image.where(collection_id=self.id).with_entities(Image.id).distinct()
            return Annotation.where(image_id__in=image_ids).count()
        except Exception as e:
            print(e)

    # TODO: separate class?
    @staticmethod 
    def guest_users_to_dict(guest_users):
        return dict([tuple(guest_user.split(':')) for guest_user in guest_users.split(';')])

    @staticmethod
    def validate_guest_users(guest_users_dict):
        """Always call before saving to DB"""
        for u in guest_users_dict:
            if not User.where(id=u).first():
                raise ValueError(f'User {u} does not exist')
            if guest_users_dict[u] not in ['read', 'write']:
                raise ValueError(f'Invalid access level {guest_users_dict[u]} for user {u}')

    @staticmethod
    def dict_to_guest_users(guest_users):
        return ';'.join([f'{user_id}:{write_access}' for user_id, write_access in guest_users.items()])

    @staticmethod
    def dict_guests_to_human_readable(guest_users_dict):
        return dict([(User.where(id=user_id).first().email, write_access) for user_id, write_access in guest_users_dict.items()])

    @staticmethod
    def get_collections_for_user(current_user_id, include_guest_access=False, include_readonly=False):
        from annotations_app.flask_app import db

        return db.session.query(ImageCollection).filter(
            or_(ImageCollection.user_id == current_user_id,
                and_(include_guest_access, 
                     current_user_id in ImageCollection.guest_users_to_dict(ImageCollection.guest_users).keys()),
                     or_(include_readonly, 
                         ImageCollection.guest_users_to_dict(ImageCollection.guest_users)[current_user_id]=='write')),
        )

    @staticmethod
    def get_collection_or_abort(collection_id, current_user_id, include_guest_access=False, include_readonly=False):
        """
        Either return first(single) collection or raise 404 exception
        """
        from flask import abort
        from annotations_app.flask_app import db

        collection = (
            ImageCollection.get_collections_for_user(current_user_id, include_guest_access, include_readonly)
            .filter(ImageCollection.id == collection_id)
            .first()
        )
        if not collection:
            abort(404, description="Collection not found")
        return collection


class Image(BaseModel):
    __tablename__ = 'images'

    id = db.Column(String(36), primary_key=True, default=uuid.uuid4)

    collection_id = db.Column(String(36), ForeignKey("imagecollections.id"), nullable=False)
    created_at = db.Column(DateTime(timezone=True), default=datetime.datetime.utcnow)
    mimetype = db.Column(String(255))
    size = db.Column(Integer)
    file_hash = db.Column(String(255), default="")
    storageKey = db.Column(String(1024))
    extra_data = db.Column(Text)
    prediction_status = db.Column(Text)

    collection = relationship("ImageCollection", back_populates="images")
    annotations = relationship("Annotation", back_populates="image")
    predictions = relationship("HeadstampPrediction", back_populates="image")

    def __str__(self):
        return self.id

    @property
    def filename(self):
        try:
            return f"{self.id}.{self.storageKey.rsplit('.', maxsplit=1)[1]}"
        except Exception as e:
            print(e)
            return "file.bin"

    @staticmethod
    def get_image_or_abort(image_id, current_user_id, include_guest_access=False, include_readonly=False):
        """
        Either return first(single) image or raises an 404 exception which is handled elsewhere
        """
        from flask import abort
        from annotations_app.flask_app import db

        this_user_collections = ImageCollection.get_collections_for_user(
            current_user_id, 
            include_guest_access, 
            include_readonly)

        image_in_db = (
            db.session.query(Image)
            .filter(
                Image.collection_id.in_(this_user_collections.with_entities(ImageCollection.id).distinct()),
            )
            .filter(
                Image.id == image_id,
            )
            .first()
        )
        if not image_in_db:
            abort(404, description="Image not found")
        return image_in_db




class HeadstampPrediction(BaseModel):
    __tablename__ = 'predictions'

    id = db.Column(String(36), primary_key=True, default=uuid.uuid4)
    created_at = db.Column(DateTime(timezone=True), default=datetime.datetime.utcnow)

    image_id = db.Column(String(36), ForeignKey("images.id"))
    image = relationship("Image", back_populates="predictions")
    casing_box = db.Column(Text)
    casing_confidence = db.Column(Float)
    primer_box = db.Column(Text)
    primer_confidence = db.Column(Float)
    
    def __str__(self):
        return self.id
