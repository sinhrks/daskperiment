from daskperiment.testing import CleanupMixin, ex  # noqa
from .base import ExperimentBase


class TestMongoExperiment(ExperimentBase, CleanupMixin):

    backend = 'mongodb://localhost:27017/test_db'
