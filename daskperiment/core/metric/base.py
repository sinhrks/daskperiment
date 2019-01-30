import pandas as pd

from daskperiment.backend.base import init_backend
from daskperiment.util.text import validate_key


def init_metricmanager(protocol):
    backend = init_backend(protocol)
    return backend.get_metricmanager()


class _MetricManager(object):

    def save(self, experiment_id, metric_key, trial_id, epoch, value):
        """
        Save metrics to MetricManager
        """
        metric_key = validate_key(metric_key, keyname='Metric name')
        return self._save(experiment_id=experiment_id, metric_key=metric_key,
                          trial_id=trial_id, epoch=epoch, value=value)

    def load(self, experiment_id, metric_key, trial_id):
        """
        Loading metrics from (multiple) trial id
        """
        metric_key = validate_key(metric_key, keyname='Metric name')

        if not pd.api.types.is_list_like(trial_id):
            trial_id = [trial_id]

        metrics = [self._load_single(experiment_id=experiment_id,
                                     metric_key=metric_key,
                                     trial_id=i)
                   for i in trial_id]

        result = pd.concat(metrics, axis=1)
        result.index.name = 'Epoch'
        if isinstance(result, pd.Series):
            result = result.to_frame()
        result.columns.name = 'Trial ID'
        return result
