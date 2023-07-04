import json

from flask import request, abort
from flask_login import current_user

from annotations_app.flask_app import app, db
from annotations_app import schemas
from annotations_app.config import logging
from annotations_app.models.base import Ammunition, Image, User, ImageCollection, UserScope, PUBLIC_SCOPE_USER_ID
from annotations_app.utils import t4t_login_required, superuser_required
from sqlalchemy import and_, desc
import datetime

# TODO: what kinds of top-level filters will we want here?
@app.route("/api/v0/ammunition", methods=["GET"])
@t4t_login_required
def ammunition_list():
    """List of ammunition_classifications
    ---
    get:
      parameters:
        - in: query
          name: ammunition_id
          schema:
            type: string
          required: false
          description: The ammunition ID to filter on        
      responses:
        200:
          description: List of all ammunition records, or the record for the specified ammunition_id
          content:
            application/json:
              schema: AmmunitionListSchema
    """
    args = request.args
    ammunition_id = args.get("ammunition_id") or None
    

    # retrieve image and collection (if requested) just to ensure they exist and visible
    
    queryset = db.session.query(Ammunition).filter(
        and_(
            # filter by image
            Ammunition.id == ammunition_id if ammunition_id else True,            
        )
    )

    total = queryset.count()
    results = queryset.order_by(
        "created_date", "id",
    )

    return schemas.AmmunitionListSchema().dump(
        {
            "total": total,
            "ammunitions": results,
        }
    )


@app.route("/api/v0/ammunition/<string:ammunition_id>", methods=["GET"])
@t4t_login_required
def ammunition_detail(ammunition_id: str):
    """Return requested ammunition information as JSON
    ---
    get:
      parameters:
        - in: path
          name: ammunition_id
          schema:
            type: string
          required: true
          description: Unique ammunition ID
      responses:
        200:
          description: JSON with the ammunition info
          content:
            application/json:
              schema: AmmunitionDisplaySchema
    """
    ammunition_in_db = Ammunition.get_or_abort(ammunition_id)
    return schemas.AmmunitionDisplaySchema().dump(ammunition_in_db)


def validate_or_create_reference_collection(req):
    reference_collection = req.get('reference_collection', None)
    if reference_collection:
        collection = ImageCollection.get_collection_or_abort(reference_collection, current_user.id, include_guest_access=True)
        public_scope = any(filter(lambda x: x.user_id == PUBLIC_SCOPE_USER_ID, collection.userscopes))
        if (not public_scope):
            abort(400, "Reference collection must have a public scope")
    if req.get('headstamp_image', None):
        hs_image = Image.get_image_or_abort(req['headstamp_image'], current_user.id, include_guest_access=True)  # ensure exists and available
        if reference_collection and hs_image.collection_id != reference_collection:
            abort(400, "Headstamp and profile images must be from the same valid reference collection")
        reference_collection = hs_image.collection_id
    if req.get('profile_image', None):
        pr_image = Image.get_image_or_abort(req['profile_image'], current_user.id, include_guest_access=True)
        if reference_collection and pr_image.collection_id != reference_collection:
            abort(400, "Headstamp and profile images must be from the same reference collection")
        reference_collection = pr_image.collection_id
    
    if reference_collection is None:
        # First try finding a reference collection        
        reference_collection_in_db = ImageCollection.get_reference_collections().first()
        if reference_collection_in_db is not None:
            reference_collection = reference_collection_in_db.id
        else:  # Not found so create one
            reference_collection = ImageCollection(
                user_id=current_user.id,            
                name="Ammunition Reference Collection",            
            )
            db.session.add(reference_collection)
            db.session.commit()
            db.session.refresh(reference_collection)
            userscope_in_db = UserScope(
                user_id=PUBLIC_SCOPE_USER_ID,
                imagecollection_id=reference_collection.id,            
                access_level='read',
            )
            db.session.add(userscope_in_db)
            db.session.commit()
            logging.info("Created reference collection %s", reference_collection.id)
            reference_collection = reference_collection.id
    return reference_collection

@app.route("/api/v0/ammunition", methods=["POST"])
@superuser_required
def ammunition_post():
    """Create annotation for image
    ---
    post:
        requestBody:
          content:
            application/json:
              schema:
                type: object
                properties:
                  caliber:
                    type: string
                  cartridge_type:
                    type: string
                  casing_material:
                    type: string
                  country:
                    type: string
                  manufacturer:
                    type: string
                  year_start:
                    type: integer
                  year_end:
                    type: integer
                  headstamp_markings:
                    type: string
                  projectile:
                    type: string
                  casing_description:
                    type: string
                  primer:
                    type: string
                  data_source:
                    type: string
                  notes:
                    type: string
                  reference_collection:
                    type: string
                  headstamp_image:
                    type: string
                  profile_image:
                    type: string                      
        responses:
            201:
              description: Details about the created annotation
              content:
                application/json:
                  schema: AmmunitionDisplaySchema
    """
    logging.info("Uploading ammunition for user %s", current_user.id)

    req = request.get_json()
    reference_collection = validate_or_create_reference_collection(req)
    logging.info(f"reference collection: {reference_collection}")
    # create database object if succesfull
    ammunition_in_db = Ammunition(
        caliber=req.get('caliber', None),
        cartridge_type=req.get('cartridge_type', None),
        casing_material=req.get('casing_material', None),
        country=req.get('country', None),
        manufacturer=req.get('manufacturer', None),
        year_start=int(req.get('year_start', 0)),
        year_end=int(req.get('year_end', 0)),
        headstamp_markings=req.get('headstamp_markings', None),
        projectile=req.get('projectile', None),
        casing_description=req.get('casing_description', None),
        primer=req.get('primer', None),
        data_source=req.get('data_source', None),
        notes=req.get('notes', None),
        reference_collection=reference_collection,
        headstamp_image=req.get('headstamp_image', None),
        profile_image=req.get('profile_image', None),
        created_by = current_user.id,
        updated_by = current_user.id,
    )
    db.session.add(ammunition_in_db)
    db.session.commit()
    db.session.refresh(ammunition_in_db)
    return schemas.AmmunitionDisplaySchema().dump(ammunition_in_db), 201


@app.route("/api/v0/ammunition/<string:ammunition_id>", methods=["PUT"])
@t4t_login_required
def ammunition_replace(ammunition_id):
    """Replace/update ammunition
    ---
    put:
        parameters:
        - in: path
          name: ammunition_id
          schema:
            type: string
          required: true
          description: Unique ammunition ID
        requestBody:
          content:
            application/json:
              schema:
                type: object
                properties:
                  caliber:
                    type: string
                  cartridge_type:
                    type: string
                  casing_material:
                    type: string
                  country:
                    type: string
                  manufacturer:
                    type: string
                  year_start:
                    type: integer
                  year_end:
                    type: integer
                  headstamp_markings:
                    type: string
                  projectile:
                    type: string
                  casing_description:
                    type: string
                  primer:
                    type: string
                  data_source:
                    type: string
                  reference_collection:
                    type: string
                  notes:
                    type: string
                  headstamp_image:
                    type: string
                  profile_image:
                    type: string              
        responses:
            201:
              description: Details about the updated annotation
              content:
                application/json:
                  schema: AnnotationDisplaySchema
    """
    logging.info("PUT ammunition request for user %s", current_user.id)

    # TODO: validate the payload.
    # TODO: escape quotes and other dangerous chars
    req = request.get_json()

    
    ammunition_in_db = Ammunition.get_or_abort(ammunition_id)

    reference_collection = validate_or_create_reference_collection(req)
    logging.info(f"reference collection: {reference_collection}")
    
    ammunition_in_db.caliber = req.get('caliber', None) or ammunition_in_db.caliber
    ammunition_in_db.cartridge_type = req.get('cartridge_type', None) or ammunition_in_db.cartridge_type
    ammunition_in_db.casing_material = req.get('casing_material', None) or ammunition_in_db.casing_material
    ammunition_in_db.country = req.get('country', None) or ammunition_in_db.country
    ammunition_in_db.manufacturer = req.get('manufacturer', None) or ammunition_in_db.manufacturer
    ammunition_in_db.year_start = int(req.get('year_start', 0)) or ammunition_in_db.year_start
    ammunition_in_db.year_end = int(req.get('year_end', 0)) or ammunition_in_db.year_end
    ammunition_in_db.headstamp_markings = req.get('headstamp_markings', None) or ammunition_in_db.headstamp_markings
    ammunition_in_db.projectile = req.get('projectile', None) or ammunition_in_db.projectile
    ammunition_in_db.casing_description = req.get('casing_description', None) or ammunition_in_db.casing_description
    ammunition_in_db.primer = req.get('primer', None) or ammunition_in_db.primer
    ammunition_in_db.data_source = req.get('data_source', None) or ammunition_in_db.data_source
    ammunition_in_db.notes = req.get('notes', None) or ammunition_in_db.notes
    ammunition_in_db.reference_collection = reference_collection or ammunition_in_db.reference_collection
    ammunition_in_db.headstamp_image = req.get('headstamp_image', None) or ammunition_in_db.headstamp_image
    ammunition_in_db.profile_image = req.get('profile_image', None) or ammunition_in_db.profile_image
    ammunition_in_db.updated_by = current_user.id
    ammunition_in_db.updated_date = datetime.datetime.utcnow()
    
    db.session.commit()
    db.session.refresh(ammunition_in_db)
    return schemas.AmmunitionDisplaySchema().dump(ammunition_in_db)


@app.route("/api/v0/ammunition/<string:ammunition_id>", methods=["DELETE"])
@t4t_login_required
def ammunition_delete(ammunition_id):
    """Remove the ammunition record
    ---
    delete:
      parameters:
        - in: path
          name: ammunition_id
          schema:
            type: string
          required: true
          description: Unique ammunition ID
      responses:
        204:
          description: Success
    """
    logging.info("DELETE ammunition request for user %s", current_user.id)
    
    # TODO: this may orphan the headstamp and profile images.  Should we delete them too?
    ammunition_in_db = Ammunition.get_or_abort(ammunition_id)

    db.session.delete(ammunition_in_db)
    db.session.commit()
    return ("", 204)



@app.route("/api/v0/ammunition/<string:ammunition_id>/navigation", methods=["GET"])
@t4t_login_required
def ammunition_navigation(ammunition_id):
    """Get adjacent ammunition records in the database, for navigation
    ---
    get:
      parameters:
        - in: path
          name: ammunition_id
          schema:
            type: string
          required: true
          description: Unique ammunition ID
        - in: query
          name: sort_by
          schema:
            type: string
          required: false
          description: Sort by field (created_at, id)
      responses:
        200:
          description: Previous and next ammunition in the database
          content:
            application/json:
              schema: NavigationSchema
    """
    ammunition_in_db=Ammunition.get_or_abort(ammunition_id)

    sort_by = request.args.get("sort_by", "created_date")
    if sort_by not in ["created_date", "id"]:
        abort(400, description="Invalid sort_by parameter")

    # TODO: is there a cleaner way?
    if sort_by == "created_date":
        next_id = db.session.query(Ammunition.id).filter(
            Ammunition.created_date > ammunition_in_db.created_date
        ).order_by(Ammunition.created_date).limit(1).scalar()
        prev_id = db.session.query(Ammunition.id).filter(
            Ammunition.created_date < ammunition_in_db.created_date
        ).order_by(desc(Ammunition.created_date)).limit(1).scalar()
    else: # sort_by == "id"
        next_id = db.session.query(Ammunition.id).filter(
          Ammunition.id > ammunition_id
        ).order_by(Ammunition.id).limit(1).scalar()
        prev_id = db.session.query(Ammunition.id).filter(
          Ammunition.id < ammunition_id
        ).order_by(desc(Ammunition.id)).limit(1).scalar()
    return schemas.NavigationSchema().dump({
        "next": next_id,
        "prev": prev_id,
    }), 200
