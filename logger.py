import logging, logging.handlers
import sys

LOGGER_NAME = 'memberbooth'

def init_logger(logger_name=LOGGER_NAME):
    logger = logging.getLogger(logger_name)
    formatter = logging.Formatter('%(asctime)s %(levelname)s [%(process)d/%(threadName)s %(pathname)s:%(lineno)d]: %(message)s')

    # Logger to file with rotating backups and high verbosity
    fh = logging.handlers.RotatingFileHandler(logger_name + ".log", maxBytes=1e6, backupCount=5)
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    # Logger to stderr
    sh = logging.StreamHandler(sys.stderr)
    sh.setLevel(logging.WARNING)
    sh.setFormatter(formatter)
    logger.addHandler(sh)
    
def get_logger(logger_name=LOGGER_NAME):
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)
    return logger
