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
import daskperiment.io.serialize as serialize
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
        logger.info('Parameters: {}'.format(exp._parameters.describe()))

        try:
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
        # token = tokenize(func, *args, **kwargs)

        result = func(*args, **kwargs)

        path = experiment.get_persist_path(func.__name__, experiment.trial_id)
        serialize.save(result, path)
        return result

    return wrapper


class Experiment(object):

    _instance_cache = {}

    def __new__(cls, id, cache=None, backend='local'):
        # return the identical instance based on id
        if id in cls._instance_cache:
            return cls._instance_cache[id]

        obj = super().__new__(cls)

        id = validate_key(id, keyname='Experiment ID')
        obj.id = id

        if cache is None:
            dname = '{}'.format(id)
            from daskperiment.config import _CACHE_DIR
            cache = _CACHE_DIR / dname
        obj._cache = cache

        cls._instance_cache[id] = obj
        return obj

    def __init__(self, id, cache=None, backend='local'):
        """
        Automatically load myself if cached pickle file exists
        """
        # DELETEME after full Redis support
        self._local = init_backend(self._cache)
        if backend == 'local':
            backend = self._local

        path = self.get_autosave_path()
        if path.is_file():
            exp = serialize.load(path)
            self.__dict__.update(exp.__dict__)

            # Create current Environment, and check the difference from
            # pickled Environment
            env = Environment()
            env.check_diff(self._environment)
            self._environment = env
        else:
            msg = 'Initialized new experiment: {}'
            logger.info(msg.format(path))

            self._initialize(backend=backend)

        # output environment info
        self._environment.describe()
        self._save_environment()

    def __repr__(self):
        msg = 'Experiment(id: {}, trial_id: {})'
        return msg.format(self.id, self.trial_id)

    @property
    def trial_id(self):
        return self._trials.trial_id

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

    def __getnewargs__(self):
        return (self.id, self._cache)

    def save(self):
        path = self.get_autosave_path()
        serialize.save(self, path)

    def _initialize(self, backend='local'):

        self._backend = init_backend(backend)
        self._parameters = ParameterManager()

        # code management
        self._codes = CodeManager()

        # history management
        # TODO: Add Trial Manager
        from daskperiment.core.trial import LocalTrialManager
        self._trials = LocalTrialManager()

        self._metrics = self._backend.get_metricmanager()
        self._environment = Environment()

    def _delete_cache(self):
        """
        Delete cache dir
        """
        self._local._delete_cache()
        try:
            self._backend._delete_cache()
        except FileNotFoundError:
            pass

    def get_autosave_path(self):
        """
        Get Path instance to save myself
        """
        fname = '{}.pkl'.format(self.id)
        return self._local.cache_dir / fname

    def get_persist_path(self, step, trial_id):
        """
        Get Path instance to save persisted results
        """
        fname = '{}_{}_{}.pkl'.format(self.id, step, trial_id)
        return self._local.persist_dir / fname

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
        self._trials.start_trial(self._parameters)
        self._save_code()
        self.check_executable()

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

    def get_persisted(self, step, trial_id):
        self._check_trial_id(trial_id)

        path = self.get_persist_path(step, trial_id)
        return serialize.load(path)

    ##########################################################
    # Code management
    ##########################################################

    def _save_code(self):
        key = self._backend.get_code_key(self.id, self.trial_id)
        msg = 'Saving code context: {}'
        logger.info(msg.format(key))

        code_context = self._codes.describe()
        header = '# Code output saved in trial_id={}'.format(self.trial_id)
        code_context = header + os.linesep + code_context

        self._backend.save_text(key, code_context)

    def get_code(self, trial_id=None):
        if trial_id is None:
            return self._codes.describe()
        else:
            self._check_trial_id(trial_id)
            key = self._backend.get_code_key(self.id, trial_id)
            code_context = self._backend.load_text(key)

            # skip header
            codes = code_context.splitlines()[1:]
            return os.linesep.join(codes) + os.linesep

    ##########################################################
    # Metrics management
    ##########################################################

    def save_metric(self, metric_key, epoch, value):
        self._metrics.save(experiment_id=self.id, metric_key=metric_key,
                           trial_id=self.trial_id,
                           epoch=epoch, value=value)

    def load_metric(self, metric_key, trial_id):
        if not pd.api.types.is_list_like(trial_id):
            trial_id = [trial_id]

        for i in trial_id:
            self._check_trial_id(i)
        return self._metrics.load(experiment_id=self.id,
                                  metric_key=metric_key,
                                  trial_id=trial_id)

    ##########################################################
    # Environment management
    ##########################################################

    def _save_environment(self):
        """
        Save Python package info with pip freeze format
        """
        fname = 'requirements_{}.txt'
        fname = fname.format(pd.Timestamp.now().strftime('%Y%m%d%H%M%S%f'))
        path = self._local.environment_dir / fname
        self._environment.save_python_packages(path)
