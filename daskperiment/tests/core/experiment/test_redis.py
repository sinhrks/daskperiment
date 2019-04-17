import daskperiment
from daskperiment.backend import RedisBackend
from daskperiment.testing import CleanupMixin, ex  # noqa
from .base import ExperimentBase


class TestRedisExperiment(ExperimentBase, CleanupMixin):

    backend = 'redis://localhost:6379/0'

    def test_redis_init_pool(self):
        import redis
        uri = 'redis://localhost:6379/0'
        pool = redis.ConnectionPool.from_url(uri)
        exp = daskperiment.Experiment('test_redis_init_pool', backend=pool)

        assert isinstance(exp._backend, RedisBackend)

        assert exp._backend.uri == uri
        assert exp._backend.pool is pool
