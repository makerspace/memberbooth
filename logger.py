from logging import getLogger, INFO, basicConfig
import sys

LOGGER_NAME = 'memberbooth'

def init_logger(logger_name=LOGGER_NAME):
    logger = getLogger(logger_name)
    basicConfig(format='%(asctime)s %(levelname)s [%(process)d/%(threadName)s %(pathname)s:%(lineno)d]: %(message)s', stream=sys.stderr, level=INFO)
    
def get_logger(logger_name=LOGGER_NAME):
    return getLogger(logger_name)
