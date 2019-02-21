from .base import MetricManagerBase


class TestLocalMetricManager(MetricManagerBase):

    @property
    def backend(self):
        from daskperiment.config import _CACHE_DIR
        cache = _CACHE_DIR / 'local_metric_manager_test'
        return cache
