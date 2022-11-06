import os
import logging
from logging.handlers import RotatingFileHandler
from main import main
from config import Config

def create_app(config_class=Config):
    # ...
    if not main.debug and not main.testing:
        # ...

        if main.config['LOG_TO_STDOUT']:
            stream_handler = logging.StreamHandler()
            stream_handler.setLevel(logging.INFO)
            main.logger.addHandler(stream_handler)
        else:
            if not os.path.exists('logs'):
                os.mkdir('logs')
            file_handler = RotatingFileHandler('logs/main.log',
                                               maxBytes=10240, backupCount=10)
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s %(levelname)s: %(message)s '
                '[in %(pathname)s:%(lineno)d]'))
            file_handler.setLevel(logging.INFO)
            main.logger.addHandler(file_handler)

        main.logger.setLevel(logging.INFO)
        main.logger.info('Main startup')

    return main