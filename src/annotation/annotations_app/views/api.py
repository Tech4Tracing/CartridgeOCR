from flask import jsonify, render_template, request
from flask_login import login_required, current_user
from marshmallow import Schema, fields

from annotations_app import app, spec
from annotations_app.models.base import ImageCollection
from annotations_app.utils import db_session


class DemoParameter(Schema):
    gist_id = fields.Int()


class CollectionCreateSchema(Schema):
    name = fields.Str()


class CollectionDisplaySchema(Schema):
    id = fields.Str()
    # created_at = fields.DateTime()
    name = fields.Str()


class CollectionsListSchema(Schema):
    total = fields.Int()
    collections = fields.List(fields.Nested(CollectionDisplaySchema))


spec.components.schema("Collection", schema=CollectionDisplaySchema)
spec.components.schema("CollectionCreate", schema=CollectionCreateSchema)
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


@app.route("/api/v0/collections", methods=["GET"])
@login_required
def collections_get():
    """List collections
    ---
    get:
      responses:
        200:
          description: List of all collections for the given user
          content:
            application/json:
              schema: CollectionsListSchema
    """
    with db_session() as db:
        queryset = db.query(ImageCollection).filter(
            ImageCollection.user_id == current_user.id,
        )
        total = queryset.count()
        results = queryset.order_by("id")

        return CollectionsListSchema().dump(
            {
                "total": total,
                "collections": results,
            }
        )


@app.route('/api/v0/collections', methods=["POST"])
@login_required
def collections_post():
    """Create new collection
    ---
    post:
        requestBody:
          content:
            application/json:
              schema: CollectionCreateSchema
              example:
                name: the 3d bunch
        responses:
            201:
              description: The created schema content
              content:
                application/json:
                  schema: CollectionDisplaySchema
    """
    req = request.json
    # TODO: if req is None ...
    collection_in_db = ImageCollection(
        user_id=current_user.id,
        name=req["name"],
    )
    with db_session() as db:
        db.add(collection_in_db)
        db.commit()
        db.refresh(collection_in_db)
        return CollectionDisplaySchema().dump(collection_in_db)


# Register the path and the entities within it
with app.test_request_context():
    spec.path(view=collections_get)
    spec.path(view=collections_post)
