from daskperiment.backend.base import _NoSQLBackend
from daskperiment.util.log import get_logger


logger = get_logger(__name__)


class RedisBackend(_NoSQLBackend):

    _SEP = ':'

    def __init__(self, experiment_id, uri):
        super().__init__(experiment_id)

        import redis

        if isinstance(uri, redis.ConnectionPool):
            self._pool = uri

            # TODO: properly build uri from ConnectionPool
            # distinguish protocol from Pool
            uri = 'redis://{host}:{port}/{db}'.format(**uri.connection_kwargs)

        self.uri = uri

    @property
    def pool(self):
        if not hasattr(self, '_pool'):
            import redis
            self._pool = redis.ConnectionPool.from_url(self.uri)
        return self._pool

    @property
    def client(self):
        if not hasattr(self, '_client'):
            import redis
            self._client = redis.StrictRedis(connection_pool=self.pool,
                                             charset="utf-8",
                                             decode_responses=True)
        return self._client

    def get_metric_manager(self):
        from daskperiment.core.metric.nosql import RedisMetricManager
        return RedisMetricManager(backend=self)

    def get_trial_manager(self):
        from daskperiment.core.trial.nosql import RedisTrialManager
        return RedisTrialManager(backend=self)

    ################################################
    # Key & value management
    ################################################

    def build_key(self, *keys):
        keys = [str(key) for key in keys]
        return self._SEP.join(keys)

    def _get_trial_id_key(self):
        """
        Specify the key to save trial_id
        """
        return self.build_key(self.experiment_id, 'trial_id')

    def _get_parameter_key(self, trial_id):
        return self.build_key(self.experiment_id, 'parameter', trial_id)

    def _get_history_key(self, trial_id):
        return self.build_key(self.experiment_id, 'history', trial_id)

    def _get_metric_key(self, metric_key, trial_id):
        return self.build_key(self.experiment_id, 'metric',
                              metric_key, trial_id)

    def _get_persist_key(self, step, trial_id):
        return self.build_key(self.experiment_id, 'persist', step, trial_id)

    def _get_step_hash_key(self, key):
        return self.build_key(self.experiment_id, 'step_hash', key)

    def _get_code_key(self, trial_id):
        return self.build_key(self.experiment_id, 'code', trial_id)

    def _get_environment_key(self, env_key, trial_id, ext):
        # ext is used in LocalBackend
        return self.build_key(self.experiment_id, env_key, trial_id)

    ################################################
    # Low level API
    ################################################

    def set(self, key, value):
        self._validate_key(key)
        return self.client.set(key, value)

    def get(self, key):
        self._validate_key(key)
        return self.client.get(key)

    def append_list(self, key, value):
        self._validate_key(key)
        return self.client.rpush(key, value)

    def get_list(self, key):
        self._validate_key(key)
        return self.client.lrange(key, 0, -1)

    def increment(self, key):
        return self.client.incr(key)

    ################################################
    # High level API
    ################################################

    def _finalize_text(self, value):
        return value.decode('utf-8')

    def _delete_cache(self):
        self.client.flushdb()

    ################################################
    # Redis unique
    ################################################

    def keys(self, key):
        keys = self.client.keys(key)
        return [key.decode('utf-8') for key in keys]

    def get_trial_id_from_key(self, key):
        self._validate_key(key)
        if isinstance(key, str):
            key = key.rsplit(self._SEP)[-1]
        else:
            key = key.rsplit(self._SEP.encode())[-1]
        return int(key)
