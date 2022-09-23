Setup:
To set up environment to train textSnake model:
Downlod some form of conda (https://docs.conda.io/en/latest/miniconda.html)
conda create --name openmmlab python=3.8 -y
conda activate openmmlab

For GPU enivornments:
conda install pytorch torchvision -c pytorch
For CPU environments:
conda install pytorch torchvision cpuonly -c pytorch

pip install -U openmim
mim install mmcv-full
pip install mmdet
pip install mmocr



For further information:
https://mmocr.readthedocs.io/en/latest/install.html


To train run 
python End_to_end_train.py --inputPath=C:\Users\ecarlson\Desktop\azDest\export_test
from the snakeModel directory