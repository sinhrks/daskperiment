from daskperiment.backend.base import _BaseBackend
from daskperiment.core.errors import TrialIDNotFoundError
import daskperiment.io.pickle as pickle
from daskperiment.util.log import get_logger


logger = get_logger(__name__)


class RedisBackend(_BaseBackend):

    def __init__(self, experiment_id, uri):
        super().__init__(experiment_id)
        self.uri = uri

    def __getstate__(self):
        state = {}
        state['experiment_id'] = self.experiment_id
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

    @property
    def metrics(self):
        if not hasattr(self, '_metrics'):
            from daskperiment.core.metric.redis import RedisMetricManager
            self._metrics = RedisMetricManager(backend=self)
        return self._metrics

    @property
    def trials(self):
        if not hasattr(self, '_trials'):
            from daskperiment.core.trial import RedisTrialManager
            self._trials = RedisTrialManager(backend=self)
        return self._trials

    def get_persist_key(self, step, trial_id):
        """
        Get Redis key to save persisted results
        """
        return '{}:persist:{}:{}'.format(self.experiment_id, step, trial_id)

    def get_code_key(self, trial_id):
        """
        Get Redis key to save code
        """
        return '{}:code:{}'.format(self.experiment_id, trial_id)

    def get_python_package_key(self, trial_id):
        return '{}:requirements:{}'.format(self.experiment_id, trial_id)

    def get_device_info_key(self, trial_id):
        return '{}:device:{}'.format(self.experiment_id, trial_id)

    def get_trial_id_from_key(self, key):
        assert isinstance(key, (str, bytes)), key
        if isinstance(key, str):
            key = key.rsplit(':')[-1]
        else:
            key = key.rsplit(b':')[-1]
        return int(key)

    def save_text(self, key, text):
        assert isinstance(key, (str, bytes))
        self.client.set(key, text)

    def load_text(self, key):
        """
        Load code context from file
        """
        assert isinstance(key, (str, bytes)), key
        res = self.client.get(key)

        if res is None:
            raise TrialIDNotFoundError(key)
        else:
            return res.decode('utf-8')

    def save_object(self, key, obj):
        """
        Save object to key
        """
        assert isinstance(key, (str, bytes)), key
        self.client.set(key, pickle.dumps(obj))

    def load_object(self, key):
        """
        Load object from key
        """
        assert isinstance(key, (str, bytes)), key
        res = self.client.get(key)

        if res is None:
            raise TrialIDNotFoundError(key)
        else:
            return pickle.loads(res)

    def _delete_cache(self):
        self.client.flushall()
