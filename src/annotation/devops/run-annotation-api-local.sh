#!/bin/sh

cd /app
/bin/sh -c 'sleep 15 && echo Running migrations && alembic -c=/app/alembic/alembic.ini upgrade head' &
echo "Starting the app..."
# uvicorn app.main:app --host 0.0.0.0 --port 18003 --reload
#FLASK_APP=annotations_app.flask_app FLASK_ENV=development flask run -p 8080 -h 0.0.0.0
celery -A annotations_app.flask_app.celery worker &
FLASK_APP=annotations_app.flask_app FLASK_ENV=production flask run -p 8080 -h 0.0.0.0