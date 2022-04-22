from flask import jsonify, render_template
from flask_login import login_required

from annotations_app.flask_app import app, spec
from annotations_app.views import users, collections, images, annotations


@app.route("/api/v0/openapi.json", methods=["GET"])
@login_required
def openapi_json():
    return jsonify(spec.to_dict())


@app.route("/api/v0/", methods=["GET"])
@login_required
def openapi_ui():
    return render_template("swagger-ui.html")


# Register the path and the entities within it
with app.test_request_context():
    spec.path(view=collections.collections_list)
    spec.path(view=collections.collection_create)
    spec.path(view=collections.collection_delete)
    spec.path(view=images.images_list)
    spec.path(view=images.image_post)
    spec.path(view=images.image_detail)
    spec.path(view=images.image_retrieve)
    spec.path(view=images.image_delete)
    spec.path(view=images.image_annotations)
    spec.path(view=annotations.annotations_list)
    spec.path(view=annotations.annotation_post)
    spec.path(view=annotations.annotation_replace)
    spec.path(view=annotations.annotation_delete)
    spec.path(view=users.users_list)
    spec.path(view=users.user_create)
    spec.path(view=users.user_update)
