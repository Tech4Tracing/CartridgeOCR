pushd ../model
python setup.py sdist bdist_wheel
popd
cd ..
export MODEL_FOLDER=/mnt/c/GitHub/CartridgeOCR/data/models/khaki_pear_9fpn66rg/

mkdir docker_context
cp model/dist/t4t_headstamp-*.whl docker_context
cp -a predict_api docker_context
cp docker_context/predict_api/.env.docker docker_context/predict_api/.env
cp -a model docker_context
cp -a $MODEL_FOLDER docker_context/model_snapshot
# remove spurious model snapshots
rm -f docker_context/model_snapshot/model_*.pth
cd docker_context
docker build -f predict_api/Dockerfile -t cartridgeocr/predict_api:latest .
cd ..
rm -rf docker_context
echo "Container built: run with 'docker run -p 8081:8081 cartridgeocr/predict_api:latest'"