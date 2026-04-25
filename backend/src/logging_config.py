import logging
from logging.config import dictConfig


def configure_logging() -> logging.Logger:
  dictConfig(
    {
      'version': 1,
      'disable_existing_loggers': False,
      'formatters': {
        'default': {
          'format': '%(asctime)s %(levelname)s [%(name)s] %(message)s',
        }
      },
      'handlers': {
        'console': {
          'class': 'logging.StreamHandler',
          'formatter': 'default',
          'level': 'INFO',
        }
      },
      'root': {
        'handlers': ['console'],
        'level': 'INFO',
      },
    }
  )
  return logging.getLogger('graphite.backend')