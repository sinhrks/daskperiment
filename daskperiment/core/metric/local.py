from daskperiment.core.errors import TrialIDNotFoundError
from daskperiment.core.metric.base import _MetricManager


class LocalMetricManager(_MetricManager):

    def __init__(self, backend):
        super().__init__(backend)
        self.metrics = {}

    def keys(self):
        return list(self.metrics.keys())

    def _save(self, metric_key, trial_id, record):
        if metric_key not in self.metrics:
            self.metrics[metric_key] = Metric(metric_key)
        self.metrics[metric_key].save(trial_id, record)

    def _load_single(self, metric_key, trial_id):
        try:
            values = self.metrics[metric_key]._load_single(trial_id)
        except KeyError:
            msg = 'Unable to find saved metric with specified key: {}'
            raise ValueError(msg.format(metric_key))

        return self._wrap_single_result(values, trial_id)


class Metric(object):

    def __init__(self, metric_key):
        self.values = {}
        self.metric_key = metric_key

    def save(self, trial_id, record):
        if trial_id not in self.values:
            self.values[trial_id] = []
        self.values[trial_id].append(record)

    def _load_single(self, trial_id):
        """
        Loading single metric from single trial id
        """
        try:
            return self.values[trial_id]
        except KeyError:
            # TODO: read from file
            raise TrialIDNotFoundError(trial_id)
