import json

import requests
from apispec import APISpec
from apispec_webframeworks.flask import FlaskPlugin
from apispec.ext.marshmallow import MarshmallowPlugin
from dotenv import load_dotenv
from flask import Flask, g, redirect, request, url_for, jsonify
from flask_login import (
    LoginManager,
    login_required,
    login_user,
    logout_user,
)
from flask_sqlalchemy import SQLAlchemy
from oauthlib.oauth2 import WebApplicationClient

from annotations_app.config import Config, logging
from werkzeug.middleware.proxy_fix import ProxyFix
import annotations_app.tasks as tasks

load_dotenv()

# TODO: fix navigation - annotated vs unannotated, collections, user-owned vs global
# TODO: annotation modes - radial vs simple bounding box vs free polygon
# TODO: text/metadata options - symbols, etc
# TODO: control points
# TODO: add casing detection model and pre-compute detections
# TODO: mouseover polygon color change
# TODO: better db representation of metadata, geometry
# TODO: deal with unusual image shapes, enable zoom, panning, etc. tiling very large images
# TODO: double-check replace events are updating the annotation id correctly.
# TODO: adding more images
# TODO: e2e image processing pipeline/user experience


spec = APISpec(
    title="Annotations API",
    version="1.0.0",
    openapi_version="3.0.2",
    plugins=[FlaskPlugin(), MarshmallowPlugin()],
)

app = Flask(__name__)
app.secret_key = Config.SECRET_KEY
app.config["SQLALCHEMY_DATABASE_URI"] = Config.SQLALCHEMY_DATABASE_URI
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config.update(CELERY_CONFIG={
    'broker_url': Config.CELERY_BROKER_URL,
    'result_backend': 'db+'+Config.SQLALCHEMY_DATABASE_URI,
})

celery = tasks.make_celery(app)
app.wsgi_app = ProxyFix(app.wsgi_app)

# Add the echo option below to enable SQL query logging
db = SQLAlchemy(app, engine_options={'pool_size': 10, 'max_overflow': 20}) #, engine_options={"echo": True})

# logging.info('Launching login manager')
# User session management setup
# https://flask-login.readthedocs.io/en/latest
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = '/'

# OAuth 2 client setup
client = WebApplicationClient(Config.GOOGLE_CLIENT_ID)


@app.errorhandler(400)
def bad_request(e):
    return jsonify({
        "errors": [
            {
                "status": "400",
                "detail": str(e)
            },
        ]
    }), 400


@app.errorhandler(404)
def resource_not_found(e):
    return jsonify({
        "errors": [
            {
                "status": "404",
                "detail": str(e)
            },
        ]
    }), 404


@app.errorhandler(500)
def internal_server_error(e):
    return jsonify({
        "errors": [
            {
                "status": "500",
                "detail": str(e)
            },
        ]
    }), 500


# Flask-Login helper to retrieve a user from our db
@login_manager.user_loader
def load_user(user_id):
    from annotations_app.user import User
    u = User.get(user_id)
    if not u or not u.is_active:
        return None  # returning None means that user won't be allowed to login
    return u


# TODO: maybe this should move to utils?
# or use database connection as context manager instead of `g`
@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_db', None)
    if db is not None:
        logging.info("Disposing the DB...")
        db.engine.dispose()
        g._db = None


# Reference for GOOG oauth: https://realpython.com/flask-google-login/
def get_google_provider_cfg():
    if not Config.GOOGLE_PROVIDER_CFG:
        Config.GOOGLE_PROVIDER_CFG = requests.get(Config.GOOGLE_DISCOVERY_URL).json()
    return Config.GOOGLE_PROVIDER_CFG


@app.route("/login")
def login():
    """
    Loging endpoints just redirects user to the Google 3rd party auth url (which returns them back later)
    """
    # Use library to construct the request for Google login and provide
    # scopes that let you retrieve user's profile from Google
    request_uri = client.prepare_request_uri(
        get_google_provider_cfg()["authorization_endpoint"],
        redirect_uri=request.base_url + "/callback",
        scope=["openid", "email", "profile"],
    )
    return redirect(request_uri)


@app.route("/login/callback")
def google_callback():
    """
    Callback endpoint handles Google 3rd party auth response and either logs in the user
    or fails the thing
    """
    from annotations_app.user import User

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
        auth=(Config.GOOGLE_CLIENT_ID, Config.GOOGLE_CLIENT_SECRET),
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
    default_fields = {
        "provider_id": provider_id,
        "name": users_name,
        "email": users_email,
        "profile_pic": picture,
    }

    user_from_db = User.get(provider_id=provider_id, default_fields=default_fields)
    if not user_from_db:
        # retry with email and provider- this will stub out a new user for admin approval.
        user_from_db = User.get(
            email=users_email,
            provider_id=provider_id,
            default_fields=default_fields
        )
        if not user_from_db:
            return "This email is not in whitelist for private beta, please ask staff to add you", 403

    logging.info("User %s login (%s)", user_from_db.email, user_from_db.provider_id)
    login_user(user_from_db)  # begin the session
    return redirect(url_for("index"))


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))
