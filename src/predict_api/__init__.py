import flask_app
# from annotations_app.models import User
# from annotations_app import views

import views.api # NOQA

if __name__ == "__main__":
    flask_app.app.run(ssl_context="adhoc")
