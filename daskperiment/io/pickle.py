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
    logger.debug(msg.format(obj, path))

    with path.open(mode='wb') as p:
        pickle.dump(obj, p)


def load(path):
    assert isinstance(path, pathlib.Path), path
    with path.open(mode='rb') as p:
        obj = pickle.load(p)
    msg = 'Loaded {} from path={}'
    logger.debug(msg.format(obj, path))
    return obj


def maybe_create_dir(name, path, parents=True):
    """
    Create new direcory if not exists
    """
    assert isinstance(path, pathlib.Path)

    if path.is_dir():
        msg = 'Use existing {} directory: {}'
        logger.debug(msg.format(name, path.absolute()))
    elif path.is_file():
        msg = 'Unable to create {} directory, the same file exists: {}'
        raise FileExistsError(msg.format(name, path.absolute()))
    else:
        msg = 'Creating new {} directory: {}'
        logger.debug(msg.format(name, path.absolute()))
        path.mkdir(parents=True)
