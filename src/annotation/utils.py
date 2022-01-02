from flask import g
import sqlite3


DATABASE = 'annotations.db'

def parse_boolean(value):
    value = value.lower()

    if value in ["true", "yes", "y", "1", "t"]:
        return True
    elif value in ["false", "no", "n", "0", "f"]:
        return False

    return False


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

def get_global(key):
    cur = get_db().cursor()
    result = cur.execute("SELECT value FROM globals WHERE key=='{}'".format(key))
    result = next(cur, [None])
    return result['value'] if result else None