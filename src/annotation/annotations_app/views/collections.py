from flask import request, abort
from flask_login import login_required, current_user

from annotations_app.flask_app import app, db
from annotations_app import schemas
from annotations_app.models.base import ImageCollection, Image, User


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
    queryset = ImageCollection.get_collections_for_user(
      current_user.id, include_guest_access=True, include_readonly=True)
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
    new_collection = ImageCollection(
        user_id=current_user.id,
        name=req["name"],
    )
    db.session.add(new_collection)
    db.session.commit()
    db.session.refresh(new_collection)
    db.session.expunge(new_collection)
    return schemas.CollectionDisplaySchema().dump(new_collection), 201


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
        204:
          description: Success
    """
    collection_in_db = db.session.query(ImageCollection).filter(
        ImageCollection.id == collection_id,
        ImageCollection.user_id == current_user.id,
    ).first()
    if not collection_in_db:
        abort(404)

    first_existing_image = (
        db.session.query(Image).filter(
            Image.collection_id == collection_in_db.id,
        ).first()
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
    db.session.delete(collection_in_db)
    db.session.commit()
    return ("", 204)



@app.route("/api/v0/collections/<string:collection_id>/guests", methods=["GET"])
@login_required
def collections_guests_list(collection_id):
    """List all guest users associated with a collection
    ---
    get:
      responses:
        200:
          description: List all guest users associated with a collection
          content:
            application/json:
              schema: CollectionGuestsSchema
    """
    collection_in_db = ImageCollection.get_collection_or_abort(collection_id, current_user.id)
    guests_dict = ImageCollection.dict_guests_to_human_readable(ImageCollection.guest_users_to_dict(collection_in_db.guest_users))
    return schemas.CollectionGuestsSchema().dump(
        {
            "guests": guests_dict,            
        }
    )


@app.route("/api/v0/collections/<string:collection_id>/guests", methods=["PUT"])
@login_required
def collections_guests_add(collection_id):
    """List all guest users associated with a collection
    ---
    put:
      requestBody:
        content:
          application/json:
            schema: CollectionGuestsRequestSchema
            example:
              email: someone@example.com
              scope: read
      responses:
        201:
          description: List all guest users associated with a collection
          content:
            application/json:
              schema: CollectionGuestsSchema
    """
    collection_in_db = ImageCollection.get_collection_or_abort(collection_id, current_user.id)
    guests_dict = ImageCollection.guest_users_to_dict(collection_in_db.guest_users)

    req = request.json
    user_email = req['email']
    user_scope = req['scope']
    user_id = User.get_user_id_by_email(user_email)
    
    if user_id is None or user_id==current_user.id:
        abort(400, description="Invalid user email")
        
    if user_scope not in ['read', 'write']:
        abort(400, description="Invalid user scope")

    guests_dict[user_id] = user_scope
    collection_in_db.guest_users = ImageCollection.dict_guests_to_db(guests_dict)
    db.session.commit()
    db.session.refresh(collection_in_db)
    guests_dict = ImageCollection.dict_guests_to_human_readable(
      ImageCollection.guest_users_to_dict(collection_in_db)
    )
    return schemas.CollectionGuestsSchema().dump(
        {
            "guests": guests_dict,            
        }
    )


@app.route("/api/v0/collections/<string:collection_id>/guests", methods=["DELETE"])
@login_required
def collections_guests_add(collection_id):
    """Delete a guest user associated with a collection
    ---
    put:
      requestBody:
        content:
          application/json:
            schema: CollectionGuestsRequestSchema
            example:
              email: someone@example.com
              scope: read  # ignored
      responses:
        201:
          description: List all guest users associated with a collection
          content:
            application/json:
              schema: CollectionGuestsSchema
    """
    collection_in_db = ImageCollection.get_collection_or_abort(collection_id, current_user.id)
    guests_dict = ImageCollection.guest_users_to_dict(collection_in_db.guest_users)

    req = request.json
    user_email = req['email']
    user_id = User.get_user_id_by_email(user_email)
    
    if user_id is None or user_id not in guests_dict:
        abort(400, description="Invalid user email")

    del guests_dict[user_id]

    collection_in_db.guest_users = ImageCollection.dict_guests_to_db(guests_dict)
    db.session.commit()
    db.session.refresh(collection_in_db)
    guests_dict = ImageCollection.dict_guests_to_human_readable(
      ImageCollection.guest_users_to_dict(collection_in_db)
    )
    return schemas.CollectionGuestsSchema().dump(
        {
            "guests": guests_dict,            
        }
    )