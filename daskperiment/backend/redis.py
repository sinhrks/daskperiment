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

    def set(self, key, value):
        return self.client.set(key, value)

    def get(self, key):
        return self.client.get(key)

    def keys(self, key):
        return self.client.keys(key)

    def append_list(self, key, value):
        return self.client.rpush(key, value)

    def get_list(self, key):
        return self.client.lrange(key, 0, -1)

    def increment(self, key):
        return self.client.incr(key)

    def _delete_cache(self):
        self.client.flushdb()
