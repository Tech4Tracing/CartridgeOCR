from flask import request, abort
from flask_login import login_required, current_user

from annotations_app import app, schemas
from annotations_app.models.base import ImageCollection, Image
from annotations_app.utils import db_session


@app.route("/api/v0/collections", methods=["GET"])
@login_required
def collections_list():
    """List all collections visible to user
    ---
    get:
      responses:
        200:
          description: List all collections visible to user
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

        return schemas.CollectionsListSchema().dump(
            {
                "total": total,
                "collections": results,
            }
        )


@app.route("/api/v0/collections", methods=["POST"])
@login_required
def collection_create():
    """Create new collection
    ---
    post:
        requestBody:
          content:
            application/json:
              schema: CollectionCreateSchema
              example:
                name: findings-2022-03-15
        responses:
            201:
              description: The created collection details
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
        return schemas.CollectionDisplaySchema().dump(collection_in_db)


@app.route("/api/v0/collections/<string:collection_id>", methods=["DELETE"])
@login_required
def collection_delete(collection_id: str):
    """Remove empty collection
    ---
    delete:
      parameters:
        - in: path
          name: collection_id
          schema:
            type: string
          required: true
          description: Unique collection ID
      responses:
        202:
          description: Success
    """
    with db_session() as db:
        collection_in_db = (
            db.query(ImageCollection)
            .filter(
                ImageCollection.id == collection_id,
                ImageCollection.user_id == current_user.id,
            )
            .first()
        )
        if not collection_in_db:
            abort(404)

        first_existing_image = (
            db.query(Image)
            .filter(
                Image.collections.any(ImageCollection.id.in_([collection_in_db.id])),
            )
            .first()
        )

        if first_existing_image:
            return (
                schemas.Errors().dump(
                    {
                        "errors": [
                            {
                                "title": "ValidationError",
                                "detail": "The collection has images - delete them first",
                            }
                        ]
                    }
                ),
                400,
            )

        db.delete(collection_in_db)
        db.commit()
        return ("", 204)
