from daskperiment.testing import CleanupMixin
from .base import MetricManagerBase


class TestRedisMetricManager(MetricManagerBase, CleanupMixin):

    backend = 'redis://localhost:6379/0'
