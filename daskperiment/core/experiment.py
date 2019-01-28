import functools
import pathlib

import numpy as np
import pandas as pd
import dask

# from dask.base import tokenize
from dask.delayed import Delayed, DelayedLeaf

from daskperiment.core.code import CodeManager
from daskperiment.core.environment import Environment
from daskperiment.core.errors import (ParameterUndeclaredError,
                                      TrialIDNotFoundError)
from daskperiment.core.metric import MetricManager
from daskperiment.core.parameter import ParameterManager, Undefined
from daskperiment.core.parser import parse_command_arguments
import daskperiment.io.serialize as serialize
from daskperiment.util.log import get_logger


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

        path = experiment.get_persist_path(func.__name__, experiment._trial_id)
        serialize.save(result, path)
        return result

    return wrapper


class Experiment(object):

    _instance_cache = {}

    def __new__(cls, id, cache=None):
        # return the identical instance based on id
        if id in cls._instance_cache:
            return cls._instance_cache[id]

        obj = super().__new__(cls)

        assert isinstance(id, str)

        obj.id = id

        if cache is None:
            dname = '{}'.format(id)
            from daskperiment.config import _CACHE_DIR
            cache = _CACHE_DIR / dname
        obj._cache = cache

        cls._instance_cache[id] = obj
        return obj

    def __init__(self, id, cache=None):
        """
        Automatically load myself if cached pickle file exists
        """
        cache_dir = self.cache_dir
        serialize.maybe_create_dir('cache', cache_dir)

        path = self.get_autosave_path()
        if path.is_file():
            exp = serialize.load(path)
            self.__dict__.update(exp.__dict__)

            # Create current Environment, and check the difference with
            # pickled Environment
            env = Environment()
            env.check_diff(self._environment)
            self._environment = env
        else:
            msg = 'Initialized new experiment: {}'
            logger.info(msg.format(path))

            self._initialize()
        # output environment info
        self._environment.describe()

    def __repr__(self):
        msg = 'Experiment(id: {}, trial_id: {})'
        return msg.format(self.id, self._trial_id)

    @property
    def cache_dir(self):
        return pathlib.Path(self._cache)

    ##########################################################
    # Parameter
    ##########################################################

    def parameter(self, name):
        return self._parameters.define(name)

    def set_parameters(self, **kwargs):
        self._parameters.set(**kwargs)

    def get_parameters(self, trial_id):
        self._check_trial_id(trial_id)
        return self._parameters_history[trial_id].to_dict()

    ##########################################################
    # Save / load myself
    ##########################################################

    def __getnewargs__(self):
        return (self.id, self._cache)

    def save(self):
        path = self.get_autosave_path()
        serialize.save(self, path)

    def _initialize(self):
        self._trial_id = 0

        self._parameters = ParameterManager()
        self._result = False

        # code management
        self._codes = CodeManager()

        # history management
        self._parameters_history = {}
        self._result_history = {}

        self._environment = Environment()
        # TODO: move metrics management to sql
        self._metrics = MetricManager()

    def _delete_cache(self):
        """
        Delete cache dir
        """
        import shutil
        shutil.rmtree(self.cache_dir)

    def get_autosave_path(self):
        """
        Get Path instance to save myself
        """
        fname = '{}.pkl'.format(self.id)
        return self.cache_dir / fname

    @property
    def persist_dir(self):
        if not hasattr(self, '_persist_dir'):
            persist_dir = self.cache_dir / 'persist'
            serialize.maybe_create_dir('persist', persist_dir)
            self._persist_dir = persist_dir
        return self._persist_dir

    def get_persist_path(self, step, trial_id):
        """
        Get Path instance to save persisted results
        """
        fname = '{}_{}_{}.pkl'.format(self.id, step, trial_id)
        return self.persist_dir / fname

    @property
    def code_dir(self):
        if not hasattr(self, '_code_dir'):
            code_dir = self.cache_dir / 'code'
            serialize.maybe_create_dir('code', code_dir)
            self._code_dir = code_dir
        return self._code_dir

    def get_code_path(self, trial_id):
        """
        Get Path instance to save code
        """
        fname = '{}_{}.txt'.format(self.id, trial_id)
        return self.code_dir / fname

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
        # increment trial id before experiment start
        self._trial_id += 1
        self._start_time = pd.Timestamp.now()

        msg = 'Started Experiment (trial id={})'
        logger.info(msg.format(self._trial_id))

        self._parameters_history[self._trial_id] = self._parameters.copy()

        self._codes.save(self._trial_id, self.get_code_path(self._trial_id))

        self.check_executable()

    def _finish_experiment_step(self, result, success, description):
        end_time = pd.Timestamp.now()
        record = {'Result': result,
                  'Success': success,
                  'Finished': end_time,
                  'Process Time': end_time - self._start_time,
                  'Description': description}
        self._result_history[self._trial_id] = record

        msg = 'Finished Experiment (trial id={})'
        logger.info(msg.format(self._trial_id))

        self.save()

    def _check_trial_id(self, trial_id):
        if not isinstance(trial_id, int):
            msg = 'Trial id must be integer, given: {}{}'
            msg.format(trial_id, type(trial_id))
            raise TrialIDNotFoundError(msg.format(trial_id, type(trial_id)))
        if trial_id <= 0 or self._trial_id < trial_id:
            raise TrialIDNotFoundError(trial_id)

    def check_executable(self):
        """
        Check whether the current Experiment is executable.

        * Result is defined
        * Parameters are all defined
        """
        self._check_result_defined()
        self._parameters._check_all_defined()

    def _check_result_defined(self):
        if not self._result:
            msg = ('Experiment result is not set. '
                   'Use Experiment.result decorator to define it')
            raise ParameterUndeclaredError(msg)

    ##########################################################
    # History management
    ##########################################################

    def get_history(self):
        params = {k: v.to_dict() for k, v in self._parameters_history.items()}
        parameters = pd.DataFrame.from_dict(params,
                                            orient='index')
        result_index = pd.Index(['Result', 'Success', 'Finished',
                                 'Process Time', 'Description'])
        results = pd.DataFrame.from_dict(self._result_history,
                                         orient='index', columns=result_index)
        results = parameters.join(results)
        results.index.name = 'Trial ID'
        return results

    def get_persisted(self, step, trial_id):
        self._check_trial_id(trial_id)

        path = self.get_persist_path(step, trial_id)
        return serialize.load(path)

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

    def save_metric(self, key, epoch, value):
        self._metrics.save(key=key, trial_id=self._trial_id,
                           epoch=epoch, value=value)

    def load_metric(self, key, trial_id):
        if not pd.api.types.is_list_like(trial_id):
            trial_id = [trial_id]

        for i in trial_id:
            self._check_trial_id(i)
        return self._metrics.load(key=key, trial_id=trial_id)
