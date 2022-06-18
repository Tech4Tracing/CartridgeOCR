from flask import jsonify, render_template
from flask_login import login_required

from flask_app import app, spec
from views import predictions


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
    spec.path(view=predictions.headstamp_predict_post)
    
