import logging
import os

import sqlalchemy as sqldb
from flask import send_file, abort, render_template, request
from flask_login import current_user

from annotations_app.flask_app import app, db as flask_db
from annotations_app.models.base import ImageCollection, Image

# the react widget catch-all page (apart of other existing endpoints like API)
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def index(path):
    if path.startswith("api/v0/"):
        abort(404)
    if current_user.is_authenticated and current_user.is_active:
        return render_template("ui/index.html")
    elif current_user.is_authenticated:
        return render_template("inactive.html")
    else:
        return render_template("unauth.html")

