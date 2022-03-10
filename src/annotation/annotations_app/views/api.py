from flask import jsonify, render_template
from flask_login import login_required  # current_user
from marshmallow import Schema, fields

from annotations_app import app, spec


class DemoParameter(Schema):
    gist_id = fields.Int()


class CollectionSchema(Schema):
    user_email = fields.Str()
    name = fields.Str()


class CollectionsListSchema(Schema):
    total = fields.Int()
    schemas = fields.List(fields.Nested(CollectionSchema))


spec.components.schema("Collection", schema=CollectionSchema)
spec.components.schema("CollectionsList", schema=CollectionsListSchema)


@app.route('/api/v0/openapi.json', methods=["GET"])
@login_required
def openapi_json():
    # current_user
    return jsonify(spec.to_dict())


@app.route('/api/v0/', methods=["GET"])
@login_required
def openapi_ui():
    return render_template('swagger-ui.html')


@app.route('/api/v0/collections', methods=['GET', 'POST'])
@login_required
def collections_endpoint():
    """List collections or create a new one
    ---
    get:
      responses:
        200:
          description: List of all schemas for the given user
          content:
            application/json:
              schema: CollectionsListSchema
        201:
          description: The created schema content
          content:
            application/json:
              schema: CollectionSchema
    """
    # TODO: implement it in real
    return jsonify({'collections': [1, 2, 3]})


# Register the path and the entities within it
with app.test_request_context():
    spec.path(view=collections_endpoint)
