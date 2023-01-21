from flask import jsonify, render_template

from annotations_app.flask_app import app, spec
from annotations_app.views import users, collections, images, annotations, predictions
from annotations_app.utils import t4t_login_required

@app.route("/api/v0/openapi.json", methods=["GET"])
@t4t_login_required
def openapi_json():
    return jsonify(spec.to_dict())


@app.route("/api/v0/", methods=["GET"])
@t4t_login_required
def openapi_ui():
    return render_template("swagger-ui.html")


# Register the path and the entities within it
with app.test_request_context():
    spec.path(view=collections.collections_list)
    spec.path(view=collections.collection_create)
    spec.path(view=collections.collection_delete)
    spec.path(view=collections.collections_guests_add)
    spec.path(view=collections.collections_guests_list)
    spec.path(view=collections.collections_guests_delete)
    spec.path(view=images.images_list)
    spec.path(view=images.image_post)
    spec.path(view=images.image_detail)
    spec.path(view=images.image_retrieve)
    spec.path(view=images.image_link)
    spec.path(view=images.image_delete)
    spec.path(view=images.image_annotations)
    spec.path(view=images.image_predictions)
    spec.path(view=images.image_update)
    spec.path(view=images.image_navigation)
    spec.path(view=annotations.annotations_list)
    spec.path(view=annotations.annotation_post)
    spec.path(view=annotations.annotation_replace)
    spec.path(view=annotations.annotation_delete)
    spec.path(view=users.users_list)
    spec.path(view=users.user_create)
    spec.path(view=users.user_update)
    spec.path(view=predictions.get_status)
    spec.path(view=predictions.predictions_list)
    spec.path(view=predictions.prediction_post)
    spec.path(view=predictions.prediction_replace)
    spec.path(view=predictions.prediction_delete)
    
    
