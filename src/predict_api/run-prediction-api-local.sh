#!/bin/sh

cd /app
echo "Starting the app..."
# uvicorn app.main:app --host 0.0.0.0 --port 18003 --reload
FLASK_APP=flask_app FLASK_DEBUG=1 flask run -p 8081 -h 0.0.0.0
