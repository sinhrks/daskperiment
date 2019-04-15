from .base import ParallelExperimentBase
from daskperiment.testing import CleanupMixin, ex       # noqa


class TestParallelMongoExperiment(ParallelExperimentBase, CleanupMixin):

    backend = 'mongodb://localhost:27017/test_db'
