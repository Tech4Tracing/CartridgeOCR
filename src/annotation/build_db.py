#!/usr/bin/env python3

import argparse
import logging
import os

import sqlalchemy
from utils import parse_boolean

logging.basicConfig(level=logging.INFO)

parser = argparse.ArgumentParser()
parser.add_argument('--clear', type=parse_boolean, default=False)
parser.add_argument('--db_name', default='annotations.db')
parser.add_argument('--img_home', default='c:\\github\\cartridgeocr\\data\\dataset\\')
args = parser.parse_args()


if args.clear:
    os.remove(args.db_name)


class DBConnection:
    def __init__(self, _engine, _connection, _metadata):
        self.engine = _engine
        self.connection = _connection
        self.metadata = _metadata


_engine = sqlalchemy.create_engine(os.environ.get("SQLALCHEMY_URL"), poolclass=sqlalchemy.pool.SingletonThreadPool)
_connection = _engine.connect()
_metadata = sqlalchemy.MetaData(_engine)
_metadata.reflect()
db = DBConnection(_engine, _connection, _metadata)

# con = sqlite3.connect(args.db_name)
# cur = con.cursor()

# cur.execute('''CREATE TABLE IF NOT EXISTS images (img_id integer primary key, filename text)''')
# cur.execute('''CREATE TABLE IF NOT EXISTS globals (key text primary key, value text)''')
# cur.execute('''CREATE TABLE IF NOT EXISTS annotations (anno_id integer primary key, img_id integer, geometry text, annotation text, metadata text)''')
# cur.execute('''DELETE from images''')
# cur.execute('''DELETE from globals''')
# cur.execute('''DELETE FROM annotations''')
# cur.execute('''INSERT INTO globals VALUES ('img_home','{}')'''.format(args.img_home))
# con.commit()


def is_image(f):
    return f.lower().endswith('.jpg')


images_table = db.metadata.tables['images']

current_img_id = 1

for f in os.listdir(args.img_home):
    if is_image(f):
        logging.info('Adding image %s', f)
        try:
            result = db.connection.execute(images_table.insert(), {
                'img_id': current_img_id,
                "filename": f,
                # 'geometry': json.dumps(req['geometry']),
                # 'annotation': req['annotation'],
                # 'metadata': json.dumps(req['metadata'])
            })
            print(result)
        except Exception as e:
            print(e)
        # cur.execute('''INSERT INTO images VALUES (null,'{}')'''.format(f))
        current_img_id += 1
    else:
        logging.info('skipping %s', f)

# con.commit()
# con.close()
