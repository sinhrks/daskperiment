import pandas as pd

from daskperiment.util.log import get_logger


logger = get_logger(__name__)


class _TrialManager(object):

    def start_trial(self, params):
        # increment trial id BEFORE experiment start
        self.increment()

        self._start_time = pd.Timestamp.now()
        msg = 'Started Experiment (trial id={})'
        logger.info(msg.format(self.trial_id))

        return self.save_parameters(self.trial_id, params)

    def finish_trial(self, result, success, description):
        end_time = pd.Timestamp.now()
        record = {'Result': result,
                  'Success': success,
                  'Finished': end_time,
                  'Process Time': end_time - self._start_time,
                  'Description': description}
        self.save_history(self.trial_id, record)

        msg = 'Finished Experiment (trial id={})'
        logger.info(msg.format(self.trial_id))


class LocalTrialManager(_TrialManager):

    def __init__(self):
        self.trial_id = 0
        self._parameters_history = {}
        self._result_history = {}

    def increment(self):
        self.trial_id += 1
        return self.trial_id

    def save_parameters(self, trial_id, params):
        self._parameters_history[trial_id] = params.to_dict()

    def load_parameters(self, trial_id):
        return self._parameters_history[trial_id]

    def save_history(self, trial_id, record):
        self._result_history[trial_id] = record

    def get_history(self):
        params = self._parameters_history.copy()
        parameters = pd.DataFrame.from_dict(params,
                                            orient='index')
        result_index = pd.Index(['Result', 'Success', 'Finished',
                                 'Process Time', 'Description'])
        # pandas 0.22 or earlier does't support columns kw
        results = pd.DataFrame.from_dict(self._result_history,
                                         orient='index')
        results = results.reindex(columns=result_index)
        results = parameters.join(results)
        results.index.name = 'Trial ID'
        return results
