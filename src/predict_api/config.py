import os
import logging.config

from dotenv import load_dotenv

# Ideally all env variables usage should be here

load_dotenv()


class Config:
    # does nothing so far but will contain more things later
    # comma-separated list of emails; these emails will be considered superusers on each login
    AUTH_WHITELISTED_EMAILS = (os.environ.get("AUTH_WHITELISTED_EMAILS") or "").split(",")

    #SQLALCHEMY_DATABASE_URI = os.environ["SQLALCHEMY_URL"]

    GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", None)
    GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", None)
    GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"
    # Note: this value can be provided by env variables, allowing to avoid requests each app start
    # if empty - will be retrieved from GOOGLE_DISCOVERY_URL
    GOOGLE_PROVIDER_CFG = None

    SECRET_KEY = os.environ.get("SECRET_KEY") or os.urandom(24)

    MODEL_FOLDER = os.environ.get("MODEL_FOLDER", None)
    MODEL_SNAPSHOT_NAME = os.environ.get("MODEL_SNAPSHOT_NAME", None)

LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
    },
    'handlers': {
        'default': {
            'level': 'INFO',
            'formatter': 'standard',
            'class': 'logging.StreamHandler',
            'stream': 'ext://sys.stdout',  # Default is stderr
        },
    },
    'loggers': {
        '': {  # root logger
            'handlers': ['default'],
            'level': 'INFO',
            'propagate': False
        },
        'azure.core.pipeline.policies.http_logging_policy': {
            'handlers': ['default'],
            'level': 'WARNING',
            'propagate': False
        },
        '__main__': {
            'handlers': ['default'],
            'level': 'INFO',
            'propagate': False
        },
        'werkzeug': {
            'handlers': ['default'],
            'level': 'INFO',
            'propagate': False
        },
    }
}

logging.config.dictConfig(LOGGING_CONFIG)
