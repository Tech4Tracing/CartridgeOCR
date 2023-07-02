from flask import request, abort
from flask_login import current_user

from annotations_app.flask_app import app, db
from annotations_app import schemas
from annotations_app.models.base import (
    ImageCollection, Image, User, UserScope, PUBLIC_SCOPE_USER_EMAIL, PUBLIC_SCOPE_USER_ID
)
from annotations_app.repos.azure_storage_provider import (
    AzureStorageProvider as StorageProvider,
)
from annotations_app.utils import parse_boolean, t4t_login_required

import logging

@app.route("/api/v0/collections", methods=["GET"])
@t4t_login_required
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
@t4t_login_required
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
@t4t_login_required
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
        - in: query
          name: force
          schema:
            type: boolean
          required: false
      responses:
        204:
          description: Success
    """
    logging.info(f"collection delete {collection_id}")
    # Only owner can delete a collection
    collection_in_db = db.session.query(ImageCollection).filter(
        ImageCollection.id == collection_id,
        ImageCollection.user_id == current_user.id,
    ).first()
    if not collection_in_db:
        logging.info(f'Collection {collection_id} not found or not owned by user {current_user.id}')
        abort(404)

    # TODO: should we force the client to confirm deletion of an empty collection?
    if not parse_boolean(request.args.get("force")):
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
    else:
      logging.info(f'Force deleting collection {collection_id}')
      images_in_db = db.session.query(Image).filter(
          Image.collection_id == collection_in_db.id,
      ).all()
      for image_in_db in images_in_db:
        storage_provider = StorageProvider()
        storage_provider.delete_file(image_in_db.storageKey)
        db.session.delete(image_in_db)
    db.session.delete(collection_in_db)
    db.session.commit()
    return ("", 204)


@app.route("/api/v0/collections/<string:collection_id>/userscopes", methods=["GET"])
@t4t_login_required
def collections_guests_list(collection_id):
    """List all user scopes associated with a collection
    ---
    get:
      parameters:
        - in: path
          name: collection_id
          schema:
            type: string
          required: true
          description: Unique collection ID
      responses:
        200:
          description: List all user scopes associated with a collection
          content:
            application/json:
              schema: CollectionUserScopeListSchema
    """
    collection_in_db = ImageCollection.get_collection_or_abort(collection_id, current_user.id)
    return schemas.CollectionUserScopeListSchema().dump(
        {
            "userscopes": [ 
              {'user_email': User.get_user_by_id(s.user_id).email, 'access_level': s.access_level } \
                for s in collection_in_db.userscopes
            ]
        }
    )


@app.route("/api/v0/collections/<string:collection_id>/userscopes", methods=["PATCH"])
@t4t_login_required
def collections_guests_add(collection_id):
    """Add a user scope to a collection
    ---
    patch:
      parameters:
        - in: path
          name: collection_id
          schema:
            type: string
          required: true
          description: Unique collection ID
      requestBody:
        content:
          application/json:
            schema: CollectionUserScopeSchema
            example:
              user_email: someone@example.com
              access_level: read
      responses:
        201:
          description: List all guest users associated with a collection
          content:
            application/json:
              schema: CollectionUserScopeSchema
    """
    collection_in_db = ImageCollection.get_collection_or_abort(collection_id, current_user.id)
    
    req = request.json
    logging.info(f'Adding userscope to collection {collection_id}: {req}')
    user_email = req['user_email']
    user_scope = req['access_level']
    user = User.get_user_by_email(user_email)
    
    if user is None or user.id==current_user.id or \
      (user.id == PUBLIC_SCOPE_USER_ID and not current_user.is_superuser):
      abort(400, description="Invalid user email")

    if user_scope not in ['read', 'write']:
        abort(400, description="Invalid access_level: must be read or write")

    userscope_in_db = (
        db.session.query(UserScope)
        .filter(
            UserScope.imagecollection_id == collection_in_db.id,
            UserScope.user_id == user.id,            
        )
        .first()
    )

    if userscope_in_db:
        userscope_in_db.access_level = user_scope
    else:
        userscope_in_db = UserScope(
            user_id=user.id,
            imagecollection_id=collection_in_db.id,            
            access_level=user_scope,
        )
    db.session.add(userscope_in_db)
    db.session.commit()
    # TODO: this got messy while debugging. While the result is valid it could be cleaned up.
    db.session.refresh(userscope_in_db)
    # db.session.refresh(collection_in_db)
    #collection_in_db = ImageCollection.get_collection_or_abort(collection_id, current_user.id)
    #result = [s for s in collection_in_db.userscopes if s.user_id==user.id]
    #assert(len(result)==1)
    #result = result[0]
    result = userscope_in_db
    return schemas.CollectionUserScopeSchema().dump(
      {'user_email':user.email, 'access_level': result.access_level}
    ), 201


@app.route("/api/v0/collections/<string:collection_id>/userscopes", methods=["DELETE"])
@t4t_login_required
def collections_guests_delete(collection_id):
    """Delete a guest user associated with a collection
    ---
    delete:
      parameters:
        - in: path
          name: collection_id
          schema:
            type: string
          required: true
          description: Unique collection ID
      requestBody:
        content:
          application/json:
            schema: CollectionUserScopeSchema
            example:
              user_email: someone@example.com
              access_level: read  # ignored
      responses:
        204:
          description: Success
    """
    collection_in_db = ImageCollection.get_collection_or_abort(collection_id, current_user.id)
    
    req = request.json
    user_email = req['user_email']
    user = User.get_user_by_email(user_email)
    
    if user is None:
        abort(400, description="Invalid user email")

    scope_in_db = (
        db.session.query(UserScope).filter(
          UserScope.imagecollection_id == collection_in_db.id, 
          UserScope.user_id == user.id
        ).first()
    )
    assert scope_in_db is not None
    db.session.delete(scope_in_db)
    db.session.commit()
    return ("", 204)
    