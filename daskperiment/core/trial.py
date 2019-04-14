import threading

import numpy as np
import pandas as pd

from daskperiment.core.errors import (LockedTrialError,
                                      TrialIDNotFoundError)
from daskperiment.util.hashing import get_hash
from daskperiment.util.log import get_logger
from daskperiment.core.parameter import ParameterManager, Undefined


logger = get_logger(__name__)


class TrialResult(object):

    def __init__(self, result, success, finished,
                 process_time, description, seed):
        self.result = result
        if result is None:
            self.result_type = 'None'
        else:
            self.result_type = repr(type(result))
        self.success = success
        self.finished = finished
        self.process_time = process_time
        self.description = description
        self.seed = seed

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
                  'Description': self.description,
                  'Seed': self.seed}
        return record


class TrialState(object):
    """
    A class represents a single trial state during execution
    """
    def __init__(self, trial_id, experiment, seed=None):
        self._current_trial_id = trial_id
        self.experiment = experiment
        self.seed = seed
        self._running = False

    @property
    def current_trial_id(self):
        # read-only
        if self._running:
            return self._current_trial_id
        else:
            msg = "Current Trial ID only exists during a trial execution"
            raise TrialIDNotFoundError(msg)

    def __enter__(self):
        self._running = True

        self._start_time = pd.Timestamp.now()
        msg = 'Started Experiment (trial id={})'
        logger.info(msg.format(self.current_trial_id))

        self.experiment._save_experiment_step(self.current_trial_id)
        self.set_seed()

        return self

    def __exit__(self, ex_type, ex_value, trace):
        # exception must be handled in with block
        msg = 'Finished Experiment (trial id={})'
        logger.info(msg.format(self.current_trial_id))

        self.experiment._save_backend()
        self.experiment._trials.unlock()
        self._running = False

        return False

    def set_seed(self):
        if self.seed is None:
            # use experiment default
            self.seed = self.experiment._seed

        if self.seed is None:
            # If seed is not provided, generate new seed
            self.seed = np.random.randint(2 ** 32 - 1)
            msg = ('Random seed is not provided, '
                   'initialized with generated seed: {}')
            logger.info(msg.format(self.seed))
        else:
            msg = ('Random seed is initialized with given seed: {}')
            logger.info(msg.format(self.seed))

        import random
        random.seed(self.seed)
        np.random.seed(self.seed)
        return self.seed

    def save_result(self, result, success, description):
        end_time = pd.Timestamp.now()
        record = TrialResult(result=result, success=success,
                             finished=end_time,
                             process_time=end_time - self._start_time,
                             description=description, seed=self.seed)
        self.experiment._trials.save_result(self.current_trial_id, record)


class _TrialManager(object):
    """
    A class to manage trial_id and history
    """
    def __init__(self, backend):
        self.backend = backend

    def __getstate__(self):
        # do not modify my __dict__
        state = self.__dict__.copy()
        # do not pickle threading Lock
        state.pop('_lock_obj', None)
        state.pop('_lock_owner', None)
        return state

    @property
    def _lock(self):
        if not hasattr(self, '_lock_obj'):
            self._lock_obj = threading.Lock()
            self._lock_owner = threading.current_thread()
        return self._lock_obj

    def is_locked(self):
        """
        Check whether myself is locked. IOW, whether the trial is
        being executed or not.
        """
        return self._lock.locked()

    def lock(self):
        """
        Lock myself and guarantee the same Trial ID is returned during a
        single trial. Note that it doesn't lock backend (db, file, etc)
        """
        self._lock.acquire()
        self._lock_owner = threading.current_thread()

    def unlock(self):
        """
        Unlock myself.
        """
        self._lock.release()

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
            # TODO: is locked by myself?
            return self._current_trial_id
        else:
            msg = "Current Trial ID only exists during a trial execution"
            raise TrialIDNotFoundError(msg)

    def start(self, experiment, seed=None):
        # increment trial id BEFORE experiment start lock myself
        trial_id = self.increment()
        return TrialState(trial_id, experiment, seed=seed)

    ##########################################################
    # Step Management
    ##########################################################

    def maybe_pure(self, func, inputs, result):
        """
        Check whether the function is pure.

        Actually, it only compares the hash of the function result based on
        its input.
        """
        # inputs is a tuple of args, kwargs
        assert isinstance(inputs, tuple)
        assert len(inputs) == 2
        args, kwargs = inputs

        input_hash = get_hash(*args, **kwargs)
        output_hash = get_hash(result)

        input_key = func.__name__ + '-' + input_hash

        previous_hash = self._update_step_hash(input_key, output_hash)
        maybe_pure = (output_hash == previous_hash)
        if not maybe_pure:
            msg = ('Experiment step result is changed with the same input: '
                   '(step: {}, args: {}, kwargs: {})')
            logger.warning(msg.format(func.__name__, args, kwargs))
        return maybe_pure

    ##########################################################
    # Trial Management
    ##########################################################

    def save_parameters(self, trial_id, params):
        if isinstance(params, ParameterManager):
            logger.info('Parameters: {}'.format(params.describe()))
            params = params.to_dict()
        # TODO raise otherwise
        return self._save_parameters(trial_id, params)

    def save_result(self, trial_id, result):
        if isinstance(result, TrialResult):
            result = result.to_dict()
        self._save_result(trial_id, result)

    def get_history(self, verbose=False):
        params = self.get_parameter_history()
        history = self.get_result_history()

        parameters = pd.DataFrame.from_dict(params,
                                            orient='index')
        if verbose:
            result_index = ['Seed', 'Result', 'Result Type', 'Success',
                            'Finished', 'Process Time', 'Description']
        else:
            result_index = ['Result', 'Success', 'Finished',
                            'Process Time', 'Description']
        result_index = pd.Index(result_index, name='Trial ID')
        # pandas 0.22 or earlier does't support columns kw
        results = pd.DataFrame.from_dict(history,
                                         orient='index')
        results = results.reindex(columns=result_index)
        results = parameters.join(results, how='right')
        results.index.name = 'Trial ID'
        return results


class LocalTrialManager(_TrialManager):

    def __init__(self, backend):
        super().__init__(backend)
        self._trial_id = 0

        self._parameters_history = {}
        self._result_history = {}

        # store function input hash and its output hash
        self._hashes = {}

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

    def _save_parameters(self, trial_id, params):
        self._parameters_history[trial_id] = params

    def load_parameters(self, trial_id):
        return self._parameters_history[trial_id]

    def _save_result(self, trial_id, params):
        self._result_history[trial_id] = params

    def get_parameter_history(self):
        return self._parameters_history.copy()

    def get_result_history(self):
        return self._result_history.copy()

    def _update_step_hash(self, key, output_hash):
        """
        Update the hash result of experiment step. Return previous hash
        if exists.
        """
        # return previous hash if exists, otherwise returns current
        previous_hash = self._hashes.get(key, output_hash)
        # overwrite with current hash
        self._hashes[key] = output_hash
        return previous_hash


class NoSQLTrialManager(_TrialManager):

    @property
    def experiment_id(self):
        return self.backend.experiment_id

    @property
    def _trial_id_key(self):
        return self.backend.build_key(self.experiment_id, 'trial_id')

    @property
    def trial_id(self):
        """
        Return latest trial ID.
        """
        if self.is_locked():
            msg = ('Unable to use TrialManager.trial_id during trial. '
                   'Use .current_trial_id for safety.')
            raise LockedTrialError(msg)
        res = self.backend.get(self._trial_id_key)
        if res is None:
            return 0
        else:
            return int(res)

    def _increment(self):
        return self.backend.increment(self._trial_id_key)

    def _save_parameters(self, trial_id, params):
        # TODO : how to distinguish Undefined and nan?
        params = {k: v for k, v in params.items()
                  if not isinstance(v, Undefined)}
        key = self.backend.get_parameter_key(trial_id)
        self.backend.save_object(key, params)

    def load_parameters(self, trial_id):
        key = self.backend.get_parameter_key(trial_id)
        return self.backend.load_object(key)

    def _save_result(self, trial_id, params):
        key = self.backend.get_history_key(trial_id)
        self.backend.save_object(key, params)

    def get_parameter_history(self):
        keys = self.backend.keys(self.backend.get_parameter_key('*'))
        k = self.backend.get_trial_id_from_key
        return {k(key): self.backend.load_object(key) for key in keys}

    def get_result_history(self):
        keys = self.backend.keys(self.backend.get_history_key('*'))
        k = self.backend.get_trial_id_from_key
        return {k(key): self.backend.load_object(key) for key in keys}

    def _update_step_hash(self, input_hash, output_hash):
        """
        Update the hash result of experiment step. Return previous hash
        if exists.
        """
        # include experiment_id in key
        key = self.backend.get_step_hash_key(input_hash)
        # return previous hash if exists, otherwise returns current
        try:
            previous_output_hash = self.backend.load_text(key)
        except TrialIDNotFoundError:
            # it doesn't use trial id...
            previous_output_hash = output_hash
        # overwrite with current hash
        self.backend.save_text(key, output_hash)
        return previous_output_hash
