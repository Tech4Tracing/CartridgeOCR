pushd ../model
python setup.py sdist bdist_wheel
popd
cd ..
export MODEL_FOLDER=/mnt/c/GitHub/CartridgeOCR/data/models/khaki_pear_9fpn66rg/

mkdir docker_context
cp model/dist/t4t_headstamp-*.whl docker_context
cp -a annotation docker_context
cp docker_context/annotation/.env.docker docker_context/annotation/.env
cp -a model docker_context
cp -a $MODEL_FOLDER docker_context/model_snapshot
# remove spurious model snapshots
rm -f docker_context/model_snapshot/model_*.pth
cd docker_context
cp annotation/requirements.txt .
docker build -f annotation/Dockerfile -t cartridgeocr/annotations_app:latest .
cd ..
rm -rf docker_context
echo "Container built: run with 'docker run -p 8081:8081 cartridgeocr/annotations_app:latest'"