from t4t_headstamp.predictions.inference import Inference
from annotations_app.config import Config
from celery.utils.log import get_task_logger

from threading import Thread, Lock


logger = get_task_logger(__name__)
mutex = Lock()
with mutex:
    try:
        logger.info('loading inference model')
        inf = Inference()
        inf.init(modelfolder=Config.MODEL_FOLDER, checkpoint=Config.MODEL_SNAPSHOT_NAME)
        logger.info('inference model loaded')
    except Exception as e:
        logger.error(f'Error loading inference model: {e}')