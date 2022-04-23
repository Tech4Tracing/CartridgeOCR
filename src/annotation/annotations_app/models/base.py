import datetime
import uuid

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Boolean, Column, Integer, Text, String, DateTime, Table, ForeignKey
from sqlalchemy.orm import relationship

db = SQLAlchemy()


# TODO: define a relationship?
class Annotation(db.Model):
    __tablename__ = 'annotations'

    id = db.Column(String(36), primary_key=True, default=uuid.uuid4)
    image_id = db.Column(String(36))
    geometry = db.Column(Text)
    annotation = db.Column(Text)
    metadata_ = db.Column('metadata', Text)

    def __str__(self):
        return self.id


# TODO: deprecate
class Global(db.Model):
    __tablename__ = 'globals'

    key = db.Column(String(8000), primary_key=True)
    value = db.Column(Text)


class User(db.Model):
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


images_to_collections_table = Table(
    'images_to_collections_table',
    db.metadata,
    Column('image_id', ForeignKey('images.id'), primary_key=True),
    Column('collection_id', ForeignKey('imagecollections.id'), primary_key=True)
)


class ImageCollection(db.Model):
    __tablename__ = 'imagecollections'

    id = db.Column(String(36), primary_key=True, default=uuid.uuid4)
    created_at = db.Column(DateTime(timezone=True), default=datetime.datetime.utcnow())

    user_id = db.Column(String(255))
    name = db.Column(String(255))

    images = relationship(
        "Image",
        secondary=images_to_collections_table,
        back_populates="collections",
    )

    def __str__(self):
        return self.id


class Image(db.Model):
    __tablename__ = 'images'

    id = db.Column(String(36), primary_key=True, default=uuid.uuid4)
    # collection_id = db.Column(String(36), nullable=True, default=None)
    created_at = db.Column(DateTime, nullable=False, default=datetime.datetime.utcnow())
    mimetype = db.Column(String(255))
    size = db.Column(Integer)
    storageKey = db.Column(String(1024))
    extra_data = db.Column(Text)

    collections = relationship(
        "ImageCollection",
        secondary=images_to_collections_table,
        back_populates="images",
    )

    def __str__(self):
        return self.id

    @property
    def filename(self):
        try:
            return f"{self.id}.{self.storageKey.rsplit('.', maxsplit=1)[1]}"
        except Exception as e:
            print(e)
            return "file.bin"
