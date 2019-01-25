import pandas as pd


class MetricManager(object):

    def __init__(self):
        self.metrics = {}

    def save(self, key, trial_id, epoch, value):
        if key not in self.metrics:
            self.metrics[key] = Metric(key)
        self.metrics[key].save(trial_id, epoch, value)

    def load(self, key, trial_id):
        return self.metrics[key].load(trial_id)


class Metric(object):

    def __init__(self, key):
        self.values = {}
        self.key = key

    def save(self, trial_id, epoch, value):
        if trial_id not in self.values:
            self.values[trial_id] = {}
        self.values[trial_id][epoch] = value

    def load(self, trial_id):
        if not pd.api.types.is_list_like(trial_id):
            trial_id = [trial_id]

        results = [pd.Series(self.values[i], name=i)
                   for i in trial_id]
        result = pd.concat(results, axis=1)
        result.index.name = 'Epoch'
        if isinstance(result, pd.Series):
            result = result.to_frame()
        return result
