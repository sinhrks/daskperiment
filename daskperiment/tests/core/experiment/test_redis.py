from daskperiment.testing import CleanupMixin, ex  # noqa
from .base import ExperimentBase


class TestRedisExperiment(ExperimentBase, CleanupMixin):

    backend = 'redis://localhost:6379/0'
