#!/bin/bash
set -e

rm -rf /app/annotation/annotations_app/static/js \
    /app/annotation/annotations_app/static/css \
    /app/annotation/annotations_app/static/media \
    /app/annotation/annotations_app/templates/ui/index.html
cd /app/t4t-annotation-UI
yarn install
yarn build
cp /app/t4t-annotation-UI/build/index.html /app/annotation/annotations_app/templates/ui/
cp -R /app/t4t-annotation-UI/build/static/css \
    /app/t4t-annotation-UI/build/static/js \
    /app/t4t-annotation-UI/build/static/media \
    /app/t4t-annotation-UI/build/manifest.json \
    /app/annotation/annotations_app/static/
cp /app/t4t-annotation-UI/build/logo*.png /app/annotation/annotations_app/static/