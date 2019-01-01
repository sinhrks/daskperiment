from daskperiment.testing import RedisCleanupMixin
from .base import ExperimentBase


class TestRedisExperiment(ExperimentBase, RedisCleanupMixin):

    backend = 'redis://localhost:6379/0'
