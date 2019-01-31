import cloudpickle as pickle
import pathlib

from daskperiment.util.log import get_logger

logger = get_logger(__name__)


def dumps(obj):
    return pickle.dumps(obj)


def loads(obj):
    return pickle.loads(obj)


def save(obj, path):
    assert isinstance(path, pathlib.Path), path
    msg = 'Saving {} to path={}'
    logger.info(msg.format(obj, path))

    with path.open(mode='wb') as p:
        pickle.dump(obj, p)


def load(path):
    assert isinstance(path, pathlib.Path), path
    with path.open(mode='rb') as p:
        obj = pickle.load(p)
    msg = 'Loaded {} from path={}'
    logger.info(msg.format(obj, path))
    return obj


def maybe_create_dir(name, path, parents=True, info=True):
    """
    Create new direcory if not exists
    """
    assert isinstance(path, pathlib.Path)

    if info:
        log_output = logger.info
    else:
        log_output = logger.debug

    if path.is_dir():
        msg = 'Use existing {} directory: {}'
        log_output(msg.format(name, path.absolute()))
    elif path.is_file():
        msg = 'Unable to create {} directory, the same file exists: {}'
        raise FileExistsError(msg.format(name, path.absolute()))
    else:
        msg = 'Creating new {} directory: {}'
        log_output(msg.format(name, path.absolute()))
        path.mkdir(parents=True)
