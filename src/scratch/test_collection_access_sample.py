
@app.route("/api/v0/collections/test_access", methods=["GET"])
@login_required
def collections_test_access():
  """Test collections access
     ---
     get:
      parameters:
        - in: path
          name: include_guest_access
          schema:
            type: string
          required: false
          description: include guest access
        - in: path
          name: include_readonly
          schema:
            type: string
          required: false
          description: include readonly
      responses:
        200:
          description: List all collections visible to user
          content:
            application/json:
              schema: CollectionsListSchema"""
  include_guest_access =  request.args.get('include_guest_access', default=False, type=lambda v: v.lower() == 'true')
  include_readonly =  request.args.get('include_readonly', default=False, type=lambda v: v.lower() == 'true')
  logging.info(f"include_guest_access: {str(include_guest_access)} {type(include_guest_access)}")
  logging.info(f"include_readonly: {str(include_readonly)} {type(include_readonly)}")
  
  queryset = ImageCollection.get_collections_for_user(
      User.get_user_by_email("test_user@tech4tracing.org").id, include_guest_access=include_guest_access, include_readonly=include_readonly)
  total = queryset.count()
  return schemas.CollectionsListSchema().dump(
        {
            "total": total,
            "collections": queryset,
        }
    )




@app.route("/api/v0/collections/test_access", methods=["GET"])
@login_required
def collections_test_access():
  """Test collections access
     ---
      get:

      responses:
        200:
          description: List all collections visible to user
          content:
            application/json:
              schema: CollectionsListSchema"""
  
  # create two collections ownedby test_user@tech4tracing.org
  # grant access to robert.sim@gmail.com, one with readonly access and one without
  # return the image collections for robert.sim@gmail.com
  c1 = ImageCollection(
        user_id=User.get_user_by_email("test_user@tech4tracing.org").id,
        name="test_collection_1_readonly",
  )
  db.session.add(c1)
  db.session.commit()
  db.session.refresh(c1)
  scope1 = UserScope(
        user_id=current_user.id,
        imagecollection_id=c1.id,
        access_level = "read"
  )
  db.session.add(scope1)
  db.session.commit()
  c2 = ImageCollection(
        user_id=User.get_user_by_email("test_user@tech4tracing.org").id,
        name="test_collection_1_readwrite",
  )
  db.session.add(c2)
  db.session.commit()
  db.session.refresh(c2)
  scope2 = UserScope(
        user_id=current_user.id,
        imagecollection_id=c2.id,
        access_level = "write"
  )
  db.session.add(scope2)
  db.session.commit()
  
  queryset = ImageCollection.get_collections_for_user(
      current_user.id, include_guest_access=True, include_readonly=True)
  total = queryset.count()
  return schemas.CollectionsListSchema().dump(
        {
            "total": total,
            "collections": queryset,
        }
    )

