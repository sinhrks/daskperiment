import datetime
from logging import (getLogger, FileHandler, StreamHandler,
                     Formatter, INFO, DEBUG)

from daskperiment.config import _LOG_DIR


_TIME_FMT = datetime.datetime.today().strftime('%Y%m%d_%H%M%S')
_FILE_FMT = 'log_{}.log'

_FORMATTER = Formatter('%(asctime)s [%(name)s] [%(levelname)s] %(message)s')


def set_config(logger, level='INFO'):
    """
    Add config to logger
    """
    if not _LOG_DIR.exists():
        _LOG_DIR.mkdir()
    log_file = _LOG_DIR / _FILE_FMT.format(_TIME_FMT)

    # for file output
    fout = FileHandler(filename=str(log_file), mode='w')
    fout.setFormatter(_FORMATTER)
    logger.addHandler(fout)

    # for stdout
    stdout = StreamHandler()
    stdout.setFormatter(_FORMATTER)
    logger.addHandler(stdout)

    if level == 'INFO':
        logger.setLevel(INFO)
    elif level == 'DEBUG':
        logger.setLevel(DEBUG)
    else:
        msg = 'log level must be either INFO or DEBUG, given: {}'
        raise ValueError(msg.format(level))
    return logger


def get_logger(name):
    logger = getLogger(name)
    return logger


_BASE = getLogger('daskperiment')
_BASE = set_config(_BASE)
