import pandas as pd

from daskperiment.backend import RedisBackend
from daskperiment.core.errors import TrialIDNotFoundError
from daskperiment.core.metric.base import _MetricManager
import daskperiment.io.json as json


class RedisMetricManager(_MetricManager):

    def __init__(self, backend):
        if not isinstance(backend, RedisBackend):
            backend = RedisBackend(backend)
        self.backend = backend

    @property
    def client(self):
        return self.backend.client

    def _get_redis_key(self, experiment_id, metric_key, trial_id):
        return '{}:metric:{}:{}'.format(experiment_id, metric_key, trial_id)

    def _save(self, experiment_id, metric_key, trial_id, epoch, value):
        redis_key = self._get_redis_key(experiment_id, metric_key, trial_id)
        val = json.dumps(dict(Epoch=epoch, Value=value))
        self.client.rpush(redis_key, val)

    def _load_single(self, experiment_id, metric_key, trial_id):
        redis_key = self._get_redis_key(experiment_id, metric_key, trial_id)
        values = self.client.lrange(redis_key, 0, -1)

        if len(values) == 0:
            search_key = self._get_redis_key(experiment_id, metric_key, '*')
            if len(self.client.keys(search_key)) == 0:
                msg = 'Unable to find saved metric with specified key: {}'
                raise ValueError(msg.format(metric_key))
            else:
                raise TrialIDNotFoundError(trial_id)

        values = [json.loads(value) for value in values]
        df = pd.DataFrame(values)
        df = df.set_index('Epoch')
        df.columns = [trial_id]
        return df
