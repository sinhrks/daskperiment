import functools
import os

import numpy as np
import pandas as pd
import dask

from dask.delayed import Delayed, DelayedLeaf

from daskperiment.backend import init_backend
from daskperiment.core.code import CodeManager
from daskperiment.core.environment import Environment
from daskperiment.core.errors import TrialIDNotFoundError
from daskperiment.core.parameter import ParameterManager
from daskperiment.core.parser import parse_command_arguments
from daskperiment.util.log import get_logger
from daskperiment.util.text import validate_key


logger = get_logger(__name__)


class ExperimentFunction(DelayedLeaf):
    __slots__ = ('_experiment', '_obj', '_key', '_pure', '_nout')

    def __init__(self, experiment, dask_obj):
        self._experiment = experiment

        self._obj = dask_obj._obj
        self._key = dask_obj._key
        self._pure = dask_obj._pure
        self._nout = dask_obj._nout


class ResultFunction(ExperimentFunction):

    def __call__(self, *args, **kwargs):
        from dask.delayed import call_function
        res = call_function(self._obj, self._key, args, kwargs,
                            pure=self._pure, nout=self._nout)
        return Result(self._experiment, res)


class Result(Delayed):
    __slots__ = ('_experiment', '_key', 'dask', '_length')

    def __init__(self, experiment, dask_obj):
        self._experiment = experiment
        self._key = dask_obj._key
        self.dask = dask_obj.dask
        self._length = dask_obj._length

        self._experiment._result = True
        self._maybe_file()

    def compute(self, **kwargs):
        # increment trial id before experiment start
        exp = self._experiment
        exp._prepare_experiment_step()

        logger.info('Target: {}'.format(self._key))

        try:
            # save may raise errors
            exp._save_experiment_step()

            result = super().compute(**kwargs)
            exp._finish_experiment_step(result=result, success=True,
                                        description=np.nan)
            return result
        except Exception as e:
            description = '{}({})'.format(e.__class__.__name__, e)
            logger.error('Experiment failed: {}'.format(description))
            exp._finish_experiment_step(result=np.nan, success=False,
                                        description=description)
            raise

    def _maybe_file(self):
        """
        Perform computation if program is run as file
        """
        if self._experiment._environment.maybe_file():
            parameters = parse_command_arguments()
            self._experiment.set_parameters(**parameters)
            self.compute()


def persist_result(experiment, func):
    """
    Persist (cache) an intermediate step result
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        experiment._save_persist(func.__name__, result)
        return result

    return wrapper


class Experiment(object):

    _instance_cache = {}

    def __new__(cls, id, backend='local'):
        # return the identical instance based on id
        if id in cls._instance_cache:
            return cls._instance_cache[id]

        obj = super().__new__(cls)

        id = validate_key(id, keyname='Experiment ID')
        obj.id = id
        cls._instance_cache[id] = obj
        return obj

    def __init__(self, id, backend='local'):
        """
        Automatically load myself if cached pickle file exists
        """
        self._backend = init_backend(experiment_id=self.id,
                                     backend=backend)
        self._backend = self._backend.load(self.id)

        if self.trial_id != 0:
            msg = 'Loaded existing experiment: {}'
            logger.info(msg.format(self))
        else:
            msg = 'Initialized new experiment: {}'
            logger.info(msg.format(self))

        self._parameters = ParameterManager()
        self._codes = CodeManager(backend=self._backend)
        self._environment = Environment(backend=self._backend)

        # TODO: check code change

        # output environment info
        self._environment.log_environment_info()
        self._check_environment_change()

    def __repr__(self):
        msg = 'Experiment(id: {}, trial_id: {})'
        return msg.format(self.id, self.trial_id)

    @property
    def trial_id(self):
        return self._trials.trial_id

    @property
    def _trials(self):
        return self._backend.trials

    @property
    def _metrics(self):
        return self._backend.metrics

    ##########################################################
    # Parameter
    ##########################################################

    def parameter(self, name):
        return self._parameters.define(name)

    def set_parameters(self, **kwargs):
        self._parameters.set(**kwargs)

    def get_parameters(self, trial_id):
        self._check_trial_id(trial_id)
        return self._trials.load_parameters(trial_id)

    ##########################################################
    # Save / load myself
    ##########################################################

    def save(self):
        self._backend.save(self.id)

    def _delete_cache(self):
        """
        Delete cache dir
        """
        self._backend._delete_cache()

    ##########################################################
    # Decorators
    ##########################################################

    def __call__(self, func):
        dask_obj = dask.delayed(func)
        self._codes.register(func)
        return ExperimentFunction(self, dask_obj)

    def persist(self, func):
        dask_obj = dask.delayed(persist_result(self, func))
        self._codes.register(func)
        return ExperimentFunction(self, dask_obj)

    def result(self, func):
        dask_obj = dask.delayed(func)
        self._codes.register(func)
        return ResultFunction(self, dask_obj)

    ##########################################################
    # Run experiment
    ##########################################################

    def _prepare_experiment_step(self):
        # when myself is not executable, immediately raise
        # (do not store history)
        self.check_executable()

        # TODO: rethinking order
        self._trials.start_trial()

    def _save_experiment_step(self):
        trial_id = self._trials.current_trial_id
        self._trials.save_parameters(self._parameters)
        self._codes.save(trial_id)
        self._environment.save(trial_id)

    def _finish_experiment_step(self, result, success, description):
        self._trials.finish_trial(result=result, success=success,
                                  description=description)
        self.save()

    def _check_trial_id(self, trial_id):
        if not isinstance(trial_id, int):
            msg = 'Trial id must be integer, given: {}{}'
            msg.format(trial_id, type(trial_id))
            raise TrialIDNotFoundError(msg.format(trial_id, type(trial_id)))
        if trial_id <= 0 or self.trial_id < trial_id:
            raise TrialIDNotFoundError(trial_id)

    def check_executable(self):
        """
        Check whether the current Experiment is executable.

        * Parameters are all defined
        """
        self._parameters._check_all_defined()

    ##########################################################
    # History management
    ##########################################################

    def get_history(self):
        return self._trials.get_history()

    def _save_persist(self, step, result):
        trial_id = self._trials.current_trial_id
        key = self._backend.get_persist_key(step, trial_id)
        self._backend.save_object(key, result)

    def get_persisted(self, step, trial_id):
        self._check_trial_id(trial_id)

        key = self._backend.get_persist_key(step, trial_id)
        return self._backend.load_object(key)

    ##########################################################
    # Code management
    ##########################################################

    def get_code(self, trial_id=None):
        if trial_id is None:
            return self._codes.describe()
        else:
            self._check_trial_id(trial_id)
            return self._codes.load(trial_id)

    ##########################################################
    # Metrics management
    ##########################################################

    def save_metric(self, metric_key, epoch, value):
        trial_id = self._trials.current_trial_id
        self._metrics.save(metric_key=metric_key, trial_id=trial_id,
                           epoch=epoch, value=value)

    def load_metric(self, metric_key, trial_id):
        if not pd.api.types.is_list_like(trial_id):
            trial_id = [trial_id]

        for i in trial_id:
            self._check_trial_id(i)
        return self._metrics.load(metric_key=metric_key,
                                  trial_id=trial_id)

    ##########################################################
    # Environment management
    ##########################################################

    def _check_environment_change(self):
        trial_id = self.trial_id
        if trial_id > 0:
            previous = self.get_environment(trial_id)
            self._environment.check_environment_change(previous)

            previous = self.get_python_packages(trial_id)
            self._environment.check_python_packages_change(previous)

    def get_environment(self, trial_id=None):
        if trial_id is None:
            text = os.linesep.join(self._environment.get_device_info())
            return text
        else:
            self._check_trial_id(trial_id)
            return self._environment.load_device_info(trial_id)

    def get_python_packages(self, trial_id=None):
        if trial_id is None:
            text = os.linesep.join(self._environment.get_python_packages())
            return text
        else:
            self._check_trial_id(trial_id)
            return self._environment.load_python_packages(trial_id)
