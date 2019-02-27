from .base import ParallelExperimentBase
from daskperiment.testing import RedisCleanupMixin, ex       # noqa


class TestParallelRedisExperiment(ParallelExperimentBase, RedisCleanupMixin):

    backend = 'redis://localhost:6379/0'
