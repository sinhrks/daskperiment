import pathlib

from daskperiment.util.log import get_logger


logger = get_logger(__name__)


def init_backend(experiment_id, protocol):
    if issubclass(type(protocol), _BaseBackend):
        return protocol

    if maybe_redis(protocol):
        from daskperiment.backend.redis import RedisBackend
        return RedisBackend(experiment_id, protocol)
    elif isinstance(protocol, pathlib.Path):
        from daskperiment.backend.local import LocalBackend
        return LocalBackend(experiment_id, protocol)
    else:
        raise NotImplementedError(protocol)


def maybe_redis(uri):
    if not isinstance(uri, str):
        return False
    protocols = ['redis://', 'rediss://', 'unix://']
    return any(uri.startswith(p) for p in protocols)


class _BaseBackend(object):

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
