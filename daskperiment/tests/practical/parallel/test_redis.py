from .base import ParallelExperimentBase
from daskperiment.testing import CleanupMixin, ex       # noqa


class TestParallelRedisExperiment(ParallelExperimentBase, CleanupMixin):

    backend = 'redis://localhost:6379/0'
