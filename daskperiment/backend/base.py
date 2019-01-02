import pathlib

from daskperiment.util.log import get_logger


logger = get_logger(__name__)


def init_backend(experiment_id=None, backend=None):
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
    if not isinstance(uri, str):
        return False
    protocols = ['redis://', 'rediss://', 'unix://']
    return any(uri.startswith(p) for p in protocols)


class _BaseBackend(object):

    def __init__(self, experiment_id):
        self.experiment_id = experiment_id

    def save(self, experiment_id):
        """
        Save myself
        """
        # overridden in LocalBackend
        # other backends should be stateless
        return self

    def load(self, experiment_id):
        """
        Load myself
        """
        return self
