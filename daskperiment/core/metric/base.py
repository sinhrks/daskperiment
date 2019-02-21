import pandas as pd

from daskperiment.util.text import validate_key


class _MetricManager(object):

    def __init__(self, backend):
        self.backend = backend

    def save(self, metric_key, trial_id, epoch, value):
        """
        Save metrics to MetricManager
        """
        metric_key = validate_key(metric_key, keyname='Metric name')
        record = dict(Epoch=epoch, Value=value,
                      Timestamp=pd.Timestamp.now())
        return self._save(metric_key=metric_key,
                          trial_id=trial_id, record=record)

    def load(self, metric_key, trial_id):
        """
        Loading metrics from (multiple) trial id
        """
        metric_key = validate_key(metric_key, keyname='Metric name')

        if not pd.api.types.is_list_like(trial_id):
            trial_id = [trial_id]

        metrics = [self._load_single(metric_key=metric_key,
                                     trial_id=i)
                   for i in trial_id]

        # build multiple metric result
        result = pd.concat(metrics, axis=1)
        result.index.name = 'Epoch'
        if isinstance(result, pd.Series):
            result = result.to_frame()
        result.columns.name = 'Trial ID'
        return result

    def _wrap_single_result(self, values, trial_id):
        """
        Build single metric result DataFrame from list of dictself.

        Called from self._load_single()
        """
        df = pd.DataFrame(values)
        df = df.set_index('Epoch')
        df = df.drop('Timestamp', axis=1)
        df.columns = [trial_id]
        return df
