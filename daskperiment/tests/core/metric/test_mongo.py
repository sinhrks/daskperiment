from daskperiment.testing import CleanupMixin
from .base import MetricManagerBase


class TestMongoMetricManager(MetricManagerBase, CleanupMixin):

    backend = 'mongodb://localhost:27017/test_db'
