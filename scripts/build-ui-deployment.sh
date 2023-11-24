#!/bin/bash
# TODO: it's unclear whether/why this is needed versus build-ui-widget.sh
set -e

rm -rf src/annotation/annotations_app/static/js \
    src/annotation/annotations_app/static/css \
    src/annotation/annotations_app/templates/ui/index.html
pushd src/t4t-annotation-UI
yarn install
yarn build
popd
cp src/t4t-annotation-UI/build/index.html src/annotation/annotations_app/templates/ui/
cp -R src/t4t-annotation-UI/build/static/css \
    src/t4t-annotation-UI/build/static/js \
    src/t4t-annotation-UI/build/manifest.json \
    src/annotation/annotations_app/static/
cp src/t4t-annotation-UI/build/logo*.png src/annotation/annotations_app/static/