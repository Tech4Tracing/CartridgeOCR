from annotations_app import app
from annotations_app.models.base import User
from annotations_app.utils import db_session, superuser_required
from annotations_app.views import schemas


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
    with db_session() as db:
        queryset = db.query(User).order_by("id")
        total = queryset.count()

        return schemas.UserListSchema().dump(
            {
                "total": total,
                "objects": queryset,
            }
        )
