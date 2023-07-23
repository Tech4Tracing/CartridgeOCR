import json

from flask import request, abort
from flask_login import current_user

from annotations_app.flask_app import app, db
from annotations_app import schemas
from annotations_app.config import logging
from annotations_app.models.base import Ammunition, Image, User, ImageCollection, UserScope, PUBLIC_SCOPE_USER_ID
from annotations_app.utils import t4t_login_required, superuser_required
from sqlalchemy import and_, desc, or_
import datetime

# TODO: what kinds of top-level filters will we want here?
@app.route("/api/v0/search", methods=["GET"])
@t4t_login_required
def simple_search():
    """Search ammunition records by keyword
    ---
    get:
      parameters:
        - in: query
          name: q
          schema:
            type: string
          required: false
          description: Keywords to search for        
      responses:
        200:
          description: List of all ammunition records, or the record for the specified ammunition_id
          content:
            application/json:
              schema: AmmunitionListSchema
    """
    args = request.args
    query = args.get("q") or None
    logging.info(f"Simple search for {query}")

    # retrieve image and collection (if requested) just to ensure they exist and visible
    
    queryset = db.session.query(Ammunition).filter(
          or_(
              Ammunition.caliber.ilike(f"%{query}%"),
              Ammunition.manufacturer.ilike(f"%{query}%"),
              Ammunition.country.ilike(f"%{query}%"),
              Ammunition.headstamp_markings.ilike(f"%{query}%"),
              Ammunition.notes.ilike(f"%{query}%")
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
