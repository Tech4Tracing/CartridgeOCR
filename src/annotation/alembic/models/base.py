# coding: utf-8
from sqlalchemy import Column, Integer, Text
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

    key = Column(Text, primary_key=True)
    value = Column(Text)


class Image(Base):
    __tablename__ = 'images'

    img_id = Column(Integer, primary_key=True)
    filename = Column(Text)
