import datetime
import uuid

from sqlalchemy import Boolean, Column, Integer, Text, String, DateTime, Table, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
metadata = Base.metadata


# TODO: define a relationship?
class Annotation(Base):
    __tablename__ = 'annotations'

    id = Column(String(36), primary_key=True, default=uuid.uuid4)
    image_id = Column(String(36))
    geometry = Column(Text)
    annotation = Column(Text)
    metadata_ = Column('metadata', Text)

    def __str__(self):
        return self.id


# TODO: deprecate
class Global(Base):
    __tablename__ = 'globals'

    key = Column(String(8000), primary_key=True)
    value = Column(Text)


class User(Base):
    __tablename__ = 'users'

    # ID in our system
    id = Column(String(36), primary_key=True, default=uuid.uuid4)

    # for 3rd party identity providers credentials
    # something like google56789098767890 or awsiam4377437437
    provider_id = Column(String(255), default=None, nullable=True)

    # normal user info
    name = Column(String(255), nullable=False, default="")
    email = Column(String(255), nullable=False)
    profile_pic = Column(String(2048), nullable=False, default="")
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)


images_to_collections_table = Table(
    'images_to_collections_table',
    Base.metadata,
    Column('image_id', ForeignKey('images.id'), primary_key=True),
    Column('collection_id', ForeignKey('imagecollections.id'), primary_key=True)
)


class ImageCollection(Base):
    __tablename__ = 'imagecollections'

    id = Column(String(36), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow())

    user_id = Column(String(255))
    name = Column(String(255))

    images = relationship(
        "Image",
        secondary=images_to_collections_table,
        back_populates="collections"
    )

    def __str__(self):
        return self.id


class Image(Base):
    __tablename__ = 'images'

    id = Column(String(36), primary_key=True, default=uuid.uuid4)
    # collection_id = Column(String(36), nullable=True, default=None)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow())
    mimetype = Column(String(255))
    size = Column(Integer)
    storageKey = Column(String(1024))
    extra_data = Column(Text)

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
