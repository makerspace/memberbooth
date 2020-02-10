import logging, logging.handlers
import sys
import config
from colors import color

def init_logger(logger_name=None):
    if logger_name:
        config.logger_name = logger_name
    logger = logging.getLogger(config.logger_name)
    timestr  = color("%(asctime)s",  fg="blue")
    levelstr = "%(levelname)s"
    pathstr  = color("%(pathname)s", fg="cyan")
    linestr  = color("%(lineno)d",   fg="magenta")
    msgstr   = "%(message)s"
    formatter = logging.Formatter(f"{timestr} {levelstr} [{pathstr}:{linestr}]: {msgstr}")

    # Logger to file with rotating backups and high verbosity
    fh = logging.handlers.RotatingFileHandler(config.logger_name + ".log", maxBytes=1e6, backupCount=5)
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    # Logger to stderr
    sh = logging.StreamHandler(sys.stderr)
    sh.setLevel(logging.WARNING)
    sh.setFormatter(formatter)
    logger.addHandler(sh)
    
def get_logger():
    logger = logging.getLogger(config.logger_name)
    logger.setLevel(logging.DEBUG)
    return logger
