import sqlite3
import argparse
import os
import logging
from utils import parse_boolean

logging.basicConfig(level=logging.INFO)

parser = argparse.ArgumentParser()
parser.add_argument('--clear', type=parse_boolean, default=False)
parser.add_argument('--db_name', default='annotations.db')
parser.add_argument('--img_home', default='c:\\github\\cartridgeocr\\data\\dataset\\')
args = parser.parse_args()


if args.clear:
    os.remove(args.db_name)

con = sqlite3.connect(args.db_name)
cur = con.cursor()

cur.execute('''CREATE TABLE IF NOT EXISTS images (img_id integer primary key, filename text)''')
cur.execute('''CREATE TABLE IF NOT EXISTS globals (key text primary key, value text)''')
cur.execute('''CREATE TABLE IF NOT EXISTS annotations (anno_id integer primary key, img_id integer, geometry text, annotation text, metadata text)''')
cur.execute('''DELETE from images''')
cur.execute('''DELETE from globals''')
cur.execute('''DELETE FROM annotations''')
cur.execute('''INSERT INTO globals VALUES ('img_home','{}')'''.format(args.img_home))
con.commit()


def is_image(f):
    return f.lower().endswith('.jpg')

for f in os.listdir(args.img_home):
    if is_image(f):
        logging.info('Adding image {}'.format(f))
        cur.execute('''INSERT INTO images VALUES (null,'{}')'''.format(f))
    else:
        logging.info('skipping {}'.format(f))
con.commit()

con.close()