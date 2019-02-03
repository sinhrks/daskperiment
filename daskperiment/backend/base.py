import pathlib

from daskperiment.util.log import get_logger


logger = get_logger(__name__)


def init_backend(experiment_id=None, backend=None):
    """
    Initialize backend from Experiment ID and protocol.

    Prameters
    ---------
    experiment_id: str
       Experiment id
    backend: str
       Backend identifier

    Returns
    -------
    Backend: backend
    """
    if issubclass(type(backend), _BaseBackend):
        return backend

    if experiment_id is None:
        msg = ('Experiment ID is not provided. This is only allowed '
               'in package testing (otherwise, it is a package bug)')
        logger.warning(msg)
        experiment_id = 'daskperiment_package_test'

    if backend == 'local':
        # LocalBackend
        dname = '{}'.format(experiment_id)
        from daskperiment.config import _CACHE_DIR
        backend = _CACHE_DIR / dname

    if maybe_redis(backend):
        from daskperiment.backend.redis import RedisBackend
        return RedisBackend(experiment_id, backend)
    elif isinstance(backend, pathlib.Path):
        from daskperiment.backend.local import LocalBackend
        return LocalBackend(experiment_id, backend)
    else:
        raise NotImplementedError(backend)


def maybe_redis(uri):
    """
    Check whether arg should be regarded as Redis

    Prameters
    ---------
    uri: obj
       Argument to be distinguished

    Returns
    -------
    bool: maybe_redis
    """
    try:
        import redis
    except ImportError:
        return False
    if isinstance(uri, redis.ConnectionPool):
        return True
    elif not isinstance(uri, str):
        return False
    protocols = ['redis://', 'rediss://', 'unix://']
    return any(uri.startswith(p) for p in protocols)


class _BaseBackend(object):

    def __init__(self, experiment_id):
        self.experiment_id = experiment_id

    def save(self):
        """
        Save myself to specified location.

        Dababase-like backends do nothing because internal status are
        all saved during other operations.
        """
        # overridden in LocalBackend
        # other backends should be stateless
        return self

    def load(self):
        """
        Load myself from specified location.

        Dababase-like backends do nothing because internal status are
        all saved during other operations.
        """
        return self
