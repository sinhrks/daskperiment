from daskperiment.backend import RedisBackend
from daskperiment.tests.experiment.base import ExperimentBase


class TestRedisExperiment(ExperimentBase):

    backend = 'redis://localhost:6379/0'

    def setup_class(cls):
        RedisBackend(cls.backend)._delete_cache()

    def teardown_class(cls):
        RedisBackend(cls.backend)._delete_cache()
