import os
from dotenv import load_dotenv

from flask import (
    Flask, g, send_file, abort,
    redirect, jsonify, render_template,
    request, url_for
)
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
)
from oauthlib.oauth2 import WebApplicationClient
import requests

from user import User
import logging
from utils import get_db, get_global, parse_boolean
import json
import sqlalchemy as sqldb

logging.basicConfig(level=logging.INFO)
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
    return User.get(user_id)


# TODO: maybe this should move to utils?
# or use database connection as context manager instead of `g`
@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_db', None)
    if db is not None:
        db.engine.dispose()
        g._db = None


# UI routes
@app.route("/")
def index():
    if current_user.is_authenticated:
        #return (
        #    "<p>Hello, {}! You're logged in! Email: {}</p>"
        #    "<div><p>Google Profile Picture:</p>"
        #    '<img src="{}" alt="Google profile pic"></img></div>'
        #    '<a class="button" href="/logout">Logout</a>'.format(
        #        current_user.name, current_user.email, current_user.profile_pic
        #    )
        #)
        return redirect('/annotate/')
    else:
        return render_template('unauth.html') 


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
        unique_id = userinfo_response.json()["sub"]
        users_email = userinfo_response.json()["email"]
        picture = userinfo_response.json()["picture"]
        users_name = userinfo_response.json()["given_name"]
    else:
        return "User email not available or not verified by Google.", 400

    # Create a user in your db with the information provided
    # by Google
    user = User(
        id_=unique_id, name=users_name, email=users_email, profile_pic=picture
    )

    # Doesn't exist? Add it to the database.
    if not User.get(unique_id):
        User.create(unique_id, users_name, users_email, picture)

    # Begin user session by logging the user in
    login_user(user)

    # Send user back to homepage
    return redirect(url_for("index"))


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))


@app.route("/annotate/")
@app.route("/annotate/<int:id>")
@login_required
def annotate(id=None):
    show_annot = parse_boolean(request.args.get('show_annot', False))
    logging.info(f'show_annot: {id} , ({show_annot})')
    if id is None:
        db = get_db()
        images = db.metadata.tables['images']
        query = sqldb.select([sqldb.func.min(images.c.img_id).label('id')])
        if not show_annot:
            # TODO: this seems broken
            annotations = db.metadata.tables['annotations']
            query = \
                query.select_from(
                    images.outerjoin(
                        annotations,
                        images.c.img_id == annotations.c.img_id)
                ).filter(annotations.c.img_id == None)
        result = db.connection.execute(query).one()
        id = result['id']
    return render_template('annotate.html', id=id, name=current_user.name.split(' ')[0])


@app.route('/annotate/prev/<int:id>')
@login_required
def prev_image(id):
    """Move to the previous image to `id`. If show_annot is false, 
    it will be the first image < `id` which is not annotated."""
    nav_annot = parse_boolean(request.cookies.get('show_annot', False))
    logging.info(f'prev: {id} , ({nav_annot})')
    db = get_db()
    images = db.metadata.tables['images']
    query = sqldb.select([sqldb.func.max(images.c.img_id).label('id')]).where(images.c.img_id < id)
    if not nav_annot:
        annotations = db.metadata.tables['annotations']
        query = \
            query.select_from(
                images.outerjoin(
                    annotations,
                    images.c.img_id == annotations.c.img_id)
            ).filter(annotations.c.img_id == None)
    result = db.connection.execute(query).one_or_none()
    if result is not None:
        id = result['id']
    return annotate(id)


@app.route('/annotate/next/<int:id>')
@login_required
def next_image(id):
    """Move to the next image after `id`. If show_annot is false, 
    it will be the first image > `id` which is not annotated."""
    nav_annot = parse_boolean(request.cookies.get('show_annot', False))
    logging.info(f'prev: {id} , ({nav_annot})')
    db = get_db()
    images = db.metadata.tables['images']
    query = sqldb.select([sqldb.func.min(images.c.img_id).label('id')]).where(images.c.img_id > id)
    if not nav_annot:
        annotations = db.metadata.tables['annotations']
        query = \
            query.select_from(
                images.outerjoin(
                    annotations,
                    images.c.img_id == annotations.c.img_id)
            ).filter(annotations.c.img_id == None)
    result = db.connection.execute(query).one_or_none()
    if result is not None:
        id = result['id']
    return annotate(id)


# maybe this could be a static route to storage?
@app.route("/images/<int:img_id>")
@login_required
def img(img_id):
    try:
        db = get_db()
        images = db.metadata.tables['images']
        query = sqldb.select(images).where(images.c.img_id == img_id)
        result = db.connection.execute(query).one()
        logging.info('Found image {}'.format(result))
        img_home = get_global('img_home')
        logging.info(f'image root {img_home}')
        filename = os.path.join(img_home, result['filename'])
        return send_file(filename, mimetype='image/jpeg')
    except Exception as e:
        print(e)
        abort(404)


# REST methods
@app.route("/images/<int:img_id>/annotations", methods=['GET'])
@login_required
def get_annotation(img_id):
    db = get_db()
    annos = db.metadata.tables['annotations']
    query = sqldb.select(
        annos.c.anno_id,
        annos.c.geometry,
        annos.c.annotation,
        annos.c.metadata).where(annos.c.img_id == img_id)
    result = db.connection.execute(query).fetchall()
    results = []
    for row in result:
        row = dict(row)
        row['geometry'] = json.loads(row['geometry'])
        row['metadata'] = json.loads(row['metadata'])
        results.append(row)

    return jsonify(results)


@app.route("/annotations/", methods=['POST'])
@login_required
def post_annotation():
    req = request.get_json()
    logging.info("POST request: {}".format(req))

    # TODO: validate the payload.
    # TODO: escape quotes and other dangerous chars
    db = get_db()

    # anno_id , img_id , geometry , annotation , metadata
    annos = db.metadata.tables['annotations']
    result = db.connection.execute(annos.insert(), {
        'img_id': req['img_id'],
        'geometry': json.dumps(req['geometry']),
        'annotation': req['annotation'],
        'metadata': json.dumps(req['metadata'])
    })
    # cur.execute('SELECT COUNT(*) AS c FROM annotations')
    # result = next(cur, [None])['c']
    # logging.info('found {} rows'.format(result))
    return jsonify({
        "message": "Annotation posted",
        "id": result.inserted_primary_key['anno_id']
    })


@app.route("/annotations/<int:anno_id>", methods=['PUT'])
@login_required
def replace_annotation(anno_id):
    req = request.get_json()
    logging.info("PUT replace request: {}".format(req))

    # TODO: validate the payload.
    # TODO: escape quotes and other dangerous chars
    # TODO: change this to an update rather than delete/insert?
    db = get_db()
    annos = db.metadata.tables['annotations']
    upd = annos.update().where(annos.c.anno_id == anno_id).values(
        {
            'img_id': req['img_id'],
            'geometry': json.dumps(req['geometry']),
            'annotation': req['annotation'],
            'metadata': json.dumps(req['metadata'])
        }
    )
    # TODO: do we need to get/validate the return result?
    db.connection.execute(upd)

    # cur.execute('SELECT COUNT(*) AS c FROM annotations')
    # result = next(cur, [None])['c']
    # logging.info('found {} rows'.format(result))
    return jsonify({"message": "Annotation updated", "id": anno_id})


@app.route("/annotations/<int:anno_id>", methods=['DELETE'])
@login_required
def delete_annotation(anno_id):
    req = request.get_json()
    logging.info("DELETE request: {}".format(req))

    # TODO: validate the payload.
    db = get_db()
    annos = db.metadata.tables['annotations']
    db.connection.execute(annos.delete().where(annos.c.anno_id == anno_id))
    return jsonify(success=True)


if __name__ == "__main__":
    app.run(ssl_context="adhoc")