export COCR_ROOT=$1
cd ${COCR_ROOT}/src/model
python setup.py sdist bdist_wheel
cd ${COCR_ROOT}/src/
#export MODEL_FOLDER=/mnt/c/GitHub/CartridgeOCR/data/models/khaki_pear_9fpn66rg/
export MODEL_FOLDER=$2

rm -rf docker_context
mkdir docker_context
cp model/dist/t4t_headstamp-*.whl docker_context
cp -a predict_api docker_context
cp docker_context/predict_api/.env.docker docker_context/predict_api/.env
cp -a model docker_context
cp -a $MODEL_FOLDER docker_context/model_snapshot
# remove spurious model snapshots
rm -f docker_context/model_snapshot/model_*.pth