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

    userscopes = relationship("UserScope", back_populates="user")

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

class UserScope(BaseModel):
    __tablename__ = 'userscopes'
    id = db.Column(String(36), primary_key=True, default=generate_short_id)
    user_id = db.Column(String(36), ForeignKey("users.id"), nullable=False)
    imagecollection_id = db.Column(String(36), ForeignKey("imagecollections.id"), nullable=False)
    access_level = db.Column(String(8), nullable=False)

    collection = relationship("ImageCollection", back_populates="userscopes")
    user = relationship("User", back_populates="userscopes")

    def __str__(self):
        return str({'id':self.id, 'user_id':self.user_id, 'imagecollection_id':self.imagecollection_id, 'access_level':self.access_level})

class ImageCollection(BaseModel):
    __tablename__ = 'imagecollections'

    id = db.Column(String(36), primary_key=True, default=generate_short_id)
    created_at = db.Column(DateTime(timezone=True), default=datetime.datetime.utcnow)

    user_id = db.Column(String(255))
    name = db.Column(String(255))
    
    userscopes = relationship("UserScope", back_populates="collection")
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
            raise

    @property 
    def current_user_scope(self):
        from flask_login import current_user        
        if self.user_id == current_user.id:
            return 'owner'
        else:
            access_levels = [c.access_level for c in self.user_scopes if c.user_id == current_user.id]
            if len(access_levels) == 0:
                return 'none'
            else:
                return access_levels[0]

    @staticmethod
    def get_collections_for_user(current_user_id, include_guest_access=False, include_readonly=False):
        from annotations_app.flask_app import db

        return db.session.query(ImageCollection).filter(
            or_(ImageCollection.user_id == current_user_id,
                and_(include_guest_access, 
                     ImageCollection.userscopes.any(
                        and_(UserScope.user_id==current_user_id,
                            or_(include_readonly, 
                                UserScope.access_level == 'write')
                            )
                     )
                    )
               ),
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
