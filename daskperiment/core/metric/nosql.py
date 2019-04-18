from daskperiment.core.errors import TrialIDNotFoundError
from daskperiment.core.metric.base import _MetricManager
import daskperiment.io.pickle as pickle


class _NoSQLMetricManager(_MetricManager):

    @property
    def experiment_id(self):
        return self.backend.experiment_id

    def _save(self, metric_key, trial_id, record):
        key = self.backend.get_metric_key(metric_key, trial_id)
        return self.backend.append_list(key, pickle.dumps(record))

    def _load_single(self, metric_key, trial_id):
        key = self.backend.get_metric_key(metric_key, trial_id)
        values = self.backend.get_list(key)

        if values is None or len(values) == 0:
            if metric_key not in self.keys():
                msg = 'Unable to find saved metric with specified key: {}'
                raise ValueError(msg.format(metric_key))
            else:
                raise TrialIDNotFoundError(trial_id)

        values = [pickle.loads(value) for value in values]

        return self._wrap_single_result(values, trial_id)


class RedisMetricManager(_NoSQLMetricManager):

    def keys(self):
        """
        Find metric names from previous trial ids
        """
        key = self.backend.get_metric_key('*', '*')
        keys = self.backend.keys(key)

        sep = self.backend._SEP
        keys = [k.split(sep)[2] for k in keys]
        keys = sorted(list(set(keys)))
        return keys


class MongoMetricManager(_NoSQLMetricManager):

    def keys(self):
        """
        Find metric names from previous trial ids
        """
        query = self.backend.get_metric_key('*', '*')
        docs = self.backend.collection.find(query.document_meta)

        results = sorted(list(set([doc['metric_key'] for doc in docs])))
        return results
