from daskperiment.core.errors import TrialIDNotFoundError
from daskperiment.core.metric.base import _MetricManager
import daskperiment.io.pickle as pickle


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

    def _save(self, metric_key, trial_id, record):
        redis_key = self._get_redis_key(metric_key, trial_id)
        self.client.rpush(redis_key, pickle.dumps(record))

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

        values = [pickle.loads(value) for value in values]

        return self._wrap_single_result(values, trial_id)
