import pathlib

from daskperiment.core.errors import TrialIDNotFoundError
import daskperiment.io.serialize as serialize
from daskperiment.util.log import get_logger


logger = get_logger(__name__)


def init_backend(protocol):
    if issubclass(type(protocol), BaseBackend):
        return protocol

    if maybe_redis(protocol):
        return RedisBackend(protocol)
    elif isinstance(protocol, pathlib.Path):
        return LocalBackend(protocol)
    else:
        raise NotImplementedError(protocol)


def maybe_redis(uri):
    if not isinstance(uri, str):
        return False
    protocols = ['redis://', 'rediss://', 'unix://']
    return any(uri.startswith(p) for p in protocols)


class BaseBackend(object):
    pass


class LocalBackend(BaseBackend):

    def __init__(self, cache_dir):
        self.cache_dir = cache_dir
        self.initialize_backend()

    def initialize_backend(self):
        serialize.maybe_create_dir('cache', self.cache_dir)

        # do not output INFO logs child folders
        serialize.maybe_create_dir('code', self.code_dir, info=False)
        serialize.maybe_create_dir('environment', self.environment_dir,
                                   info=False)
        serialize.maybe_create_dir('persist', self.persist_dir, info=False)

    @property
    def code_dir(self):
        return self.cache_dir / 'code'

    @property
    def environment_dir(self):
        return self.cache_dir / 'environment'

    @property
    def persist_dir(self):
        return self.cache_dir / 'persist'

    def get_metricmanager(self):
        if not hasattr(self, '_mm'):
            # must be pickled
            from daskperiment.core.metric.local import LocalMetricManager
            self._mm = LocalMetricManager(self.cache_dir)
        return self._mm

    def get_code_key(self, experiment_id, trial_id):
        """
        Get Path instance to save code
        """
        fname = '{}_{}.py'.format(experiment_id, trial_id)
        return self.code_dir / fname

    def save_text(self, key, text):
        """
        Save text to key (pathlib.Path)
        """
        assert isinstance(key, pathlib.Path)
        key.write_text(text)

    def load_text(self, key):
        """
        Load text from key (pathlib.Path)
        """
        assert isinstance(key, pathlib.Path)
        return key.read_text()

    def _delete_cache(self):
        """
        Delete cache dir
        """
        import shutil
        shutil.rmtree(self.cache_dir)


class RedisBackend(BaseBackend):

    def __init__(self, uri):
        self.uri = uri

    def __getstate__(self):
        state = {}
        state['uri'] = self.uri
        # do not pickle _client
        return state

    @property
    def client(self):
        if not hasattr(self, '_client'):
            import redis
            pool = redis.ConnectionPool.from_url(self.uri)
            self._client = redis.StrictRedis(connection_pool=pool,
                                             charset="utf-8",
                                             decode_responses=True)
        return self._client

    def get_metricmanager(self):
        from daskperiment.core.metric.redis import RedisMetricManager
        return RedisMetricManager(self)

    def get_code_key(self, experiment_id, trial_id):
        """
        Get Redis key to save code
        """
        return '{}:code:{}'.format(experiment_id, trial_id)

    def save_text(self, key, text):
        assert isinstance(key, str)
        self.client.set(key, text)

    def load_text(self, key):
        """
        Load code context from file
        """
        assert isinstance(key, str)
        res = self.client.get(key)

        if res is None:
            raise TrialIDNotFoundError(key.rsplit(':')[-1])
        else:
            return res.decode('utf-8')

    def _delete_cache(self):
        self.client.flushall()
