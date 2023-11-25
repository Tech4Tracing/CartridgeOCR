from flask import abort, jsonify, request
from marshmallow import ValidationError

from annotations_app.flask_app import app, db
from annotations_app import schemas
from annotations_app.models.base import User, ImageCollection, UserScope
from annotations_app.utils import superuser_required
from annotations_app.views.collections import collection_delete

@app.route("/api/v0/users", methods=["GET"])
@superuser_required
def users_list():
    """Users list, only for superusers
    ---
    get:
      responses:
        200:
          description: List of all collections for the given user
          content:
            application/json:
              schema: UserListSchema
    """
    queryset = db.session.query(User).order_by("id")
    total = queryset.count()

    return schemas.UserListSchema().dump(
        {
            "total": total,
            "objects": queryset,
        }
    )


@app.route("/api/v0/users", methods=["POST"])
@superuser_required
def user_create():
    """Create new user (with at least email provided)
    ---
    post:
        requestBody:
          content:
            application/json:
              schema: UserCreateSchema
              example:
                name: John Smith
                email: john@smith.org
                is_superuser: true
        responses:
            201:
              description: The created user details
              content:
                application/json:
                  schema: UserDisplaySchema
    """
    req = request.json

    if not req.get("email"):
        abort(400)

    existing_user_by_email = (
        db.session.query(User).filter(User.email == req.get("email")).first()
    )

    if existing_user_by_email:
        return (
            schemas.Errors().dump(
                {
                    "errors": [
                        {
                            "title": "AlreadyExists",
                            "detail": "Email is busy / user already created - use update instead",
                        }
                    ]
                }
            ),
            400,
        )

    user_in_db = User(
        email=req.get("email"),
        name=req["name"],
        is_active=req.get("is_active"),
        is_superuser=req.get("is_superuser"),
    )
    db.session.add(user_in_db)
    db.session.commit()
    db.session.refresh(user_in_db)
    return schemas.UserDisplaySchema().dump(user_in_db), 201


@app.route("/api/v0/users/<string:user_id>", methods=["PATCH", "PUT"])
@superuser_required
def user_update(user_id):
    """Replace/update user info
    ---
    patch:
        parameters:
        - in: path
          name: user_id
          schema:
            type: string
          required: true
          description: User ID
        requestBody:
          content:
            application/json:
              schema: UserCreateSchema
              example:
                name: John Smith
                email: john@smith.org
                is_superuser: true
                is_active: true
        responses:
            201:
              description: User object after update
              content:
                application/json:
                  schema: UserDisplaySchema
    """
    try:
        validated_req = schemas.UserCreateSchema().load(request.get_json())
    except ValidationError as err:
        # TODO: convert marshmallow error to our error of known format
        return jsonify(err.messages), 400

    user_in_db = db.session.query(User).filter(User.id == user_id).first()

    if not user_in_db:
        return (
            schemas.Errors().dump(
                {
                    "errors": [
                        {
                            "title": "NotFound",
                            "detail": "No user with given ID",
                        }
                    ]
                }
            ),
            404,
        )

    for key, value in validated_req.items():
        setattr(user_in_db, key, value)

    db.session.commit()
    db.session.refresh(user_in_db)
    return schemas.UserDisplaySchema().dump(user_in_db), 201


@app.route("/api/v0/users/<string:user_id>", methods=["DELETE"])
@superuser_required
def user_delete(user_id: str):
    """Remove a user
    ---
    delete:
        parameters:
        - in: path
          name: user_id
          schema:
            type: string
          required: true
          description: User ID or email      
        responses:
            202:
              description: Success              
    """
    
    user_in_db = db.session.query(User).filter(User.id == user_id).first()
    if not user_in_db:
        user_in_db = db.session.query(User).filter(User.email == user_id).first()

    if not user_in_db:
        return (
            schemas.Errors().dump(
                {
                    "errors": [
                        {
                            "title": "NotFound",
                            "detail": "No user with given ID",
                        }
                    ]
                }
            ),
            404,
        )
    
    for scope in db.session.query(UserScope).filter(UserScope.user_id == user_in_db.id):
        db.session.delete(scope)
    collections_to_delete = []
    for collection in db.session.query(ImageCollection).filter(ImageCollection.user_id == user_in_db.id):
        collections_to_delete.append(collection.id)
    for collection_id in collections_to_delete:
        delete_collection(collection_id)
    db.session.delete(user_in_db)
    db.session.commit()
    
    return ("",202)
