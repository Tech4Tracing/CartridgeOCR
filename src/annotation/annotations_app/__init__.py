import json
import os

import requests
from apispec import APISpec
from apispec_webframeworks.flask import FlaskPlugin
from apispec.ext.marshmallow import MarshmallowPlugin
from dotenv import load_dotenv
from flask import Flask, g, redirect, request, url_for
from flask_login import (
    LoginManager,
    login_required,
    login_user,
    logout_user,
)
from oauthlib.oauth2 import WebApplicationClient

from annotations_app.user import User
from annotations_app.config import logging
from annotations_app.utils import db_session

# logging.basicConfig(level=logging.INFO)

load_dotenv()

# TODO: fix navigation - annotated vs unannotated, collections, user-owned vs global
# TODO: annotation modes - radial vs simple bounding box vs free polygon
# TODO: text/metadata options - symbols, etc
# TODO: control points
# TODO: add casing detection model and pre-compute detections
# TODO: mouseover polygon color change
# TODO: better db representation of metadata, geometry
# TODO: migrate to jquery/modern widget framework
# TODO: deal with unusual image shapes, enable zoom, panning, etc. tiling very large images
# TODO: double-check replace events are updating the annotation id correctly.
# TODO: adding more images
# TODO: host db online/ migrate to modern/robust db.
# TODO: e2e image processing pipeline/user experience
# TODO: env variable for database URI
# TODO: logout button
# TODO: beautify login page
# TODO: move to env.py?
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", None)
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", None)
GOOGLE_DISCOVERY_URL = (
    "https://accounts.google.com/.well-known/openid-configuration"
)
logging.info(f'Client_ID: {GOOGLE_CLIENT_ID}')


spec = APISpec(
    title="Annotations API",
    version="1.0.0",
    openapi_version="3.0.2",
    plugins=[FlaskPlugin(), MarshmallowPlugin()],
)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY") or os.urandom(24)

logging.info('Launching login manager')
# User session management setup
# https://flask-login.readthedocs.io/en/latest
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = '/'

# OAuth 2 client setup
logging.info('Creating google client')
client = WebApplicationClient(GOOGLE_CLIENT_ID)


# Flask-Login helper to retrieve a user from our db
@login_manager.user_loader
def load_user(user_id):
    u = User.get(user_id)
    if not u.is_active:
        # TODO: we might redirect them to some page explaining what happening instead of just
        # showing them login page again and again...
        return None  # means that user won't be logged in
    return u


# TODO: maybe this should move to utils?
# or use database connection as context manager instead of `g`
@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_db', None)
    if db is not None:
        db.engine.dispose()
        g._db = None


# Reference for GOOG oauth: https://realpython.com/flask-google-login/
def get_google_provider_cfg():
    logging.info('get_google_provider_cfg')
    return requests.get(GOOGLE_DISCOVERY_URL).json()


@app.route("/login")
def login():
    logging.info('login')
    # Find out what URL to hit for Google login
    google_provider_cfg = get_google_provider_cfg()
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]

    # Use library to construct the request for Google login and provide
    # scopes that let you retrieve user's profile from Google
    request_uri = client.prepare_request_uri(
        authorization_endpoint,
        redirect_uri=request.base_url + "/callback",
        scope=["openid", "email", "profile"],
    )
    return redirect(request_uri)


@app.route("/login/callback")
def callback():
    logging.info('login callback')
    # Get authorization code Google sent back to you
    code = request.args.get("code")
    # Find out what URL to hit to get tokens that allow you to ask for
    # things on behalf of a user
    google_provider_cfg = get_google_provider_cfg()
    token_endpoint = google_provider_cfg["token_endpoint"]

    # Prepare and send a request to get tokens! Yay tokens!
    token_url, headers, body = client.prepare_token_request(
        token_endpoint,
        authorization_response=request.url,
        redirect_url=request.base_url,
        code=code
    )
    token_response = requests.post(
        token_url,
        headers=headers,
        data=body,
        auth=(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET),
    )

    # Parse the tokens!
    client.parse_request_body_response(json.dumps(token_response.json()))

    # Now that you have tokens (yay) let's find and hit the URL
    # from Google that gives you the user's profile information,
    # including their Google profile image and email
    userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
    uri, headers, body = client.add_token(userinfo_endpoint)
    userinfo_response = requests.get(uri, headers=headers, data=body)

    # You want to make sure their email is verified.
    # The user authenticated with Google, authorized your
    # app, and now you've verified their email through Google!
    if userinfo_response.json().get("email_verified"):
        google_id = userinfo_response.json()["sub"]
        users_email = userinfo_response.json()["email"]
        picture = userinfo_response.json()["picture"]
        users_name = userinfo_response.json()["given_name"]
    else:
        return "User email not available or not verified by Google.", 400

    # Doesn't exist? Add it to the database.
    provider_id = "google" + google_id
    user_from_db = User.get(provider_id=provider_id)
    # TODO: update the user details on that step if changed?
    if not user_from_db:
        user_from_db = User.create(
            provider_id=provider_id,
            name=users_name,
            email=users_email,
            profile_pic=picture
        )
    login_user(user_from_db)  # begin the session
    return redirect(url_for("index"))


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(ssl_context="adhoc")

import annotations_app.views.generic  # NOQA
import annotations_app.views.api # NOQA
