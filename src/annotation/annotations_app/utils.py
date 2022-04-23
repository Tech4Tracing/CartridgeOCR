import logging
import os
from functools import wraps
from contextlib import contextmanager

import sqlalchemy as sqldb
from flask import g, request, current_app
from flask_login import current_user
from flask_login.config import EXEMPT_METHODS
from sqlalchemy.pool import SingletonThreadPool


def parse_boolean(value):
    if type(value) is bool:
        return value
    elif type(value) is str:    
        value = value.lower()

        if value in ["true", "yes", "y", "1", "t"]:
            return True
        elif value in ["false", "no", "n", "0", "f"]:
            return False

    return False


class DBConnection:
    def __init__(self, _engine, _connection, _metadata):
        self.engine = _engine
        self.connection = _connection
        self.metadata = _metadata


def get_db() -> DBConnection:
    if getattr(g, '_db', None) is None:
        if not os.environ.get("SQLALCHEMY_URL"):
            # Example: "mssql+pymssql://sa:Your_password123@compliance_mssql/master?charset=utf8"
            # or "postgresql://complianceuser:compliancepassword@compliance_postgres/compliancedb"
            raise Exception("Please configure SQLALCHEMY_URL")
        _engine = sqldb.create_engine(os.environ.get("SQLALCHEMY_URL"), poolclass=SingletonThreadPool)
        _connection = _engine.connect()
        _metadata = sqldb.MetaData(_engine)
        _metadata.reflect()
        g._db = DBConnection(_engine, _connection, _metadata)
    return g._db


def get_global(key):
    db = get_db()
    globals = db.metadata.tables['globals']
    query = sqldb.select([globals]).where(globals.columns.key == key)
    result = db.connection.execute(query).one()
    return result['value']


# TODO: replace it by using app.db everywhere because it's much simpler
@contextmanager
def db_session():
    if not os.environ.get("SQLALCHEMY_URL"):
        raise Exception("Please configure SQLALCHEMY_URL")
    # TODO: these 2 lines are per app, not per request
    engine = sqldb.create_engine(os.environ.get("SQLALCHEMY_URL"))
    Session = sqldb.orm.sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # these per request
    session = Session()
    try:
        yield session
        session.commit()
    except Exception as e:
        logging.exception(e)
        session.rollback()
        raise
    finally:
        session.close()


def superuser_required(func):
    """
    A copy of flask-login login_required decorator but reques is_superuser flag to be set
    """

    @wraps(func)
    def decorated_view(*args, **kwargs):
        if request.method in EXEMPT_METHODS or current_app.config.get("LOGIN_DISABLED"):
            pass
        elif not current_user.is_authenticated or not current_user.is_superuser:
            return current_app.login_manager.unauthorized()
        try:
            # current_app.ensure_sync available in Flask >= 2.0
            return current_app.ensure_sync(func)(*args, **kwargs)
        except AttributeError:  # pragma: no cover
            return func(*args, **kwargs)

    return decorated_view
