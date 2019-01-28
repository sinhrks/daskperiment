import datetime
from logging import (getLogger, FileHandler, StreamHandler,
                     Formatter, INFO, DEBUG)

from daskperiment.config import _LOG_DIR


_TIME_FMT = datetime.datetime.today().strftime('%Y%m%d_%H%M%S')
_FILE_FMT = 'log_{}.log'

_FORMATTER = Formatter('%(asctime)s [%(name)s] [%(levelname)s] %(message)s')

_LOG_LEVEL = 'INFO'

if not _LOG_DIR.exists():
    _LOG_DIR.mkdir()


def get_logger(name):
    log_file = _LOG_DIR / _FILE_FMT.format(_TIME_FMT)

    logger = getLogger(name)

    # for file output
    fout = FileHandler(filename=str(log_file), mode='w')
    fout.setFormatter(_FORMATTER)
    logger.addHandler(fout)

    # for stdout
    stdout = StreamHandler()
    stdout.setFormatter(_FORMATTER)
    logger.addHandler(stdout)

    level = _LOG_LEVEL
    if level == 'INFO':
        logger.setLevel(INFO)
    elif level == 'DEBUG':
        logger.setLevel(DEBUG)
    else:
        msg = 'log level must be either INFO or DEBUG, given: {}'
        raise ValueError(msg.format(level))
    return logger
