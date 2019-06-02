import logging, logging.handlers
import sys

LOGGER_NAME = 'memberbooth'

def init_logger():
    logger = logging.getLogger(LOGGER_NAME)
    formatter = logging.Formatter('%(asctime)s %(levelname)s [%(process)d/%(threadName)s %(pathname)s:%(lineno)d]: %(message)s')

    # Logger to file with rotating backups and high verbosity
    fh = logging.handlers.RotatingFileHandler(LOGGER_NAME + ".log", maxBytes=1e6, backupCount=5)
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    # Logger to stderr
    sh = logging.StreamHandler(sys.stderr)
    sh.setLevel(logging.WARNING)
    sh.setFormatter(formatter)
    logger.addHandler(sh)
    
def get_logger():
    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(logging.DEBUG)
    return logger
