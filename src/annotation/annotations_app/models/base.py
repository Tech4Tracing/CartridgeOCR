# coding: utf-8
import uuid

from sqlalchemy import Column, Integer, Text, String, DateTime
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
metadata = Base.metadata


class Annotation(Base):
    __tablename__ = 'annotations'

    anno_id = Column(Integer, primary_key=True)
    img_id = Column(Integer)
    geometry = Column(Text)
    annotation = Column(Text)
    metadata_ = Column('metadata', Text)


class Global(Base):
    __tablename__ = 'globals'

    key = Column(String(8000), primary_key=True)
    value = Column(Text)


class Image(Base):
    __tablename__ = 'images'

    img_id = Column(Integer, primary_key=True)
    filename = Column(Text)


class User(Base):
    __tablename__ = 'users'

    id = Column(String(255), primary_key=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    profile_pic = Column(String(2048), nullable=False)


class ImageCollection(Base):
    __tablename__ = 'imagecollections'

    id = Column(String(36), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user_id = Column(String(255))
    name = Column(String(255))
