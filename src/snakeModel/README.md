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
python End_to_end_train.py --inputPath=<root of training data folder>
--outputPath=<path to output trained weights to>
from the snakeModel directory

TODO:
- Find why the model will sometimes output all NaNs (only observed on CUDA, not CPU training)
- Make the data loader able to handle a variable number of bitmask output in order to use batching more effectively
- Organize packages and dependencies when making the inference pipeline/ combing with other parts of this project.