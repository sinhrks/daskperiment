import pandas as pd

from daskperiment.core.errors import TrialIDNotFoundError
from daskperiment.core.metric.base import _MetricManager
import daskperiment.io.json as json


class RedisMetricManager(_MetricManager):

    @property
    def client(self):
        return self.backend.client

    @property
    def experiment_id(self):
        return self.backend.experiment_id

    def keys(self):
        key = self._get_redis_key('*', '*')
        keys = self.client.keys(key)
        keys = [k.decode('utf-8').split(':')[2] for k in keys]
        keys = sorted(list(set(keys)))
        return keys

    def _get_redis_key(self, metric_key, trial_id):
        return '{}:metric:{}:{}'.format(self.experiment_id,
                                        metric_key, trial_id)

    def _save(self, metric_key, trial_id, epoch, value):
        redis_key = self._get_redis_key(metric_key, trial_id)
        val = json.dumps(dict(Epoch=epoch, Value=value))
        self.client.rpush(redis_key, val)

    def _load_single(self, metric_key, trial_id):
        redis_key = self._get_redis_key(metric_key, trial_id)
        values = self.client.lrange(redis_key, 0, -1)

        if len(values) == 0:
            search_key = self._get_redis_key(metric_key, '*')
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
