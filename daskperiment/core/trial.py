import pandas as pd

from daskperiment.core.errors import (LockedTrialError,
                                      TrialIDNotFoundError)
from daskperiment.util.log import get_logger
from daskperiment.core.parameter import ParameterManager, Undefined


logger = get_logger(__name__)


class TrialResult(object):

    def __init__(self, result, success, finished,
                 process_time, description):
        self.result = result
        if result is None:
            self.result_type = 'None'
        else:
            self.result_type = repr(type(result))
        self.success = success
        self.finished = finished
        self.process_time = process_time
        self.description = description

    def __repr__(self):
        if self.success:
            fmt = 'Result(value={}, SUCCEEDED)'
        else:
            fmt = 'Result(value={}, FAILED)'
        return fmt.format(self.result)

    def to_dict(self):
        record = {'Result': self.result,
                  'Result Type': self.result_type,
                  'Success': self.success,
                  'Finished': self.finished,
                  'Process Time': self.process_time,
                  'Description': self.description}
        return record


class _TrialManager(object):

    __lock = False

    def __init__(self, backend):
        self.backend = backend

    def is_locked(self):
        """
        Check whether myself is locked. IOW, whether the trial is
        being executed or not.
        """
        return self.__lock

    def lock(self):
        """
        Lock myself and guarantee the same Trial ID is returned during a
        single trial. Note that it doesn't lock backend (db, file, etc)
        """
        if self.is_locked():
            msg = 'Trial is already locked'
            raise LockedTrialError(msg)
        self.__lock = True

    def unlock(self):
        """
        Unlock myself.
        """
        self.__lock = False

    def increment(self):
        """
        Lock myself and returns incremented Trial ID.
        """
        self.lock()
        self._current_trial_id = self._increment()
        return self.current_trial_id

    @property
    def current_trial_id(self):
        if self.is_locked():
            return self._current_trial_id
        else:
            msg = "Current Trial ID only exists during a trial execution"
            raise TrialIDNotFoundError(msg)

    def start_trial(self):
        # increment trial id BEFORE experiment start
        self.increment()

        self._start_time = pd.Timestamp.now()
        msg = 'Started Experiment (trial id={})'
        logger.info(msg.format(self.current_trial_id))

    def finish_trial(self, result, success, description):
        end_time = pd.Timestamp.now()
        record = TrialResult(result=result, success=success,
                             finished=end_time,
                             process_time=end_time - self._start_time,
                             description=description)
        self.save_history(record)

        msg = 'Finished Experiment (trial id={})'
        logger.info(msg.format(self.current_trial_id))

        self.unlock()

    def save_parameters(self, params):
        if isinstance(params, ParameterManager):
            logger.info('Parameters: {}'.format(params.describe()))
            params = params.to_dict()
        # TODO raise otherwise
        return self._save_parameters(params)

    def save_history(self, result):
        if isinstance(result, TrialResult):
            result = result.to_dict()
        self._save_history(result)

    def get_history(self):
        params = self.get_parameter_history()
        history = self.get_result_history()

        parameters = pd.DataFrame.from_dict(params,
                                            orient='index')
        result_index = ['Result', 'Result Type', 'Success', 'Finished',
                        'Process Time', 'Description']
        result_index = pd.Index(result_index, name='Trial ID')
        # pandas 0.22 or earlier does't support columns kw
        results = pd.DataFrame.from_dict(history,
                                         orient='index')
        results = results.reindex(columns=result_index)
        results = parameters.join(results)
        results.index.name = 'Trial ID'
        return results


class LocalTrialManager(_TrialManager):

    def __init__(self, backend):
        super().__init__(backend)
        self._trial_id = 0
        self._parameters_history = {}
        self._result_history = {}

        self._lock = False

    @property
    def trial_id(self):
        """
        Return latest trial ID.
        """
        if self.is_locked():
            msg = ('Unable to use TrialManager.trial_id during trial. '
                   'Use .current_trial_id for safety.')
            raise LockedTrialError(msg)
        return self._trial_id

    def _increment(self):
        self._trial_id += 1
        return self._trial_id

    def _save_parameters(self, params):
        self._parameters_history[self.current_trial_id] = params

    def load_parameters(self, trial_id):
        return self._parameters_history[trial_id]

    def _save_history(self, params):
        self._result_history[self.current_trial_id] = params

    def get_parameter_history(self):
        return self._parameters_history.copy()

    def get_result_history(self):
        return self._result_history.copy()


class RedisTrialManager(_TrialManager):

    @property
    def client(self):
        return self.backend.client

    @property
    def experiment_id(self):
        return self.backend.experiment_id

    @property
    def _trial_id_key(self):
        return '{}:trial_id'.format(self.experiment_id)

    @property
    def trial_id(self):
        """
        Return latest trial ID.
        """
        if self.is_locked():
            msg = ('Unable to use TrialManager.trial_id during trial. '
                   'Use .current_trial_id for safety.')
            raise LockedTrialError(msg)
        res = self.backend.client.get(self._trial_id_key)
        if res is None:
            return 0
        else:
            return int(res)

    def _increment(self):
        return self.client.incr(self._trial_id_key)

    def get_parameter_key(self, trial_id):
        return '{}:parameter:{}'.format(self.experiment_id, trial_id)

    def get_history_key(self, trial_id):
        return '{}:history:{}'.format(self.experiment_id, trial_id)

    def _save_parameters(self, params):
        # TODO : how to distinguish Undefined and nan?
        params = {k: v for k, v in params.items()
                  if not isinstance(v, Undefined)}
        key = self.get_parameter_key(self.current_trial_id)
        self.backend.save_object(key, params)

    def load_parameters(self, trial_id):
        key = self.get_parameter_key(trial_id)
        return self.backend.load_object(key)

    def _save_history(self, params):
        key = self.get_history_key(self.current_trial_id)
        self.backend.save_object(key, params)

    def get_parameter_history(self):
        keys = self.client.keys(self.get_parameter_key('*'))
        k = self.backend.get_trial_id_from_key
        return {k(key): self.backend.load_object(key) for key in keys}

    def get_result_history(self):
        keys = self.client.keys(self.get_history_key('*'))
        k = self.backend.get_trial_id_from_key
        return {k(key): self.backend.load_object(key) for key in keys}
