from daskperiment.testing import RedisCleanupMixin
from .base import MetricManagerBase


class TestRedisMetricManager(MetricManagerBase, RedisCleanupMixin):

    backend = 'redis://localhost:6379/0'
