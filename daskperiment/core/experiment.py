import functools
import pathlib
import pickle

import pandas as pd
import dask

# from dask.base import tokenize
from dask.delayed import Delayed, DelayedLeaf

from daskperiment.core.environment import Environment
from daskperiment.core.errors import (ParameterUndeclaredError,
                                      ParameterUndefinedError)
from daskperiment.core.metric import MetricManager
from daskperiment.core.parameter import Parameter, Undefined
from daskperiment.util.log import get_logger

logger = get_logger(__name__)


class ResultLeaf(DelayedLeaf):
    __slots__ = ('_experiment', '_obj', '_key', '_pure', '_nout')

    def __init__(self, experiment, dask_obj):
        self._experiment = experiment

        self._obj = dask_obj._obj
        self._key = dask_obj._key
        self._pure = dask_obj._pure
        self._nout = dask_obj._nout

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

    def compute(self, **kwargs):
        # increment trial id before experiment start
        exp = self._experiment
        exp._prepare_experiment_step()

        logger.info('Target: {}'.format(self._key))
        logger.info('Parameters: {}'.format(exp.show_parameters()))

        result = super().compute(**kwargs)

        exp._finish_experiment_step(result)
        return result


def persist_result(experiment, func):
    """
    Persist (cache) an intermediate step result
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # token = tokenize(func, *args, **kwargs)

        result = func(*args, **kwargs)

        path = experiment.get_persist_path(func.__name__, experiment._trial_id)
        msg = 'Saving intermediate result (trial id={}): {}(path={})'
        logger.info(msg.format(experiment._trial_id, func.__name__, path))

        with path.open(mode='wb') as p:
            pickle.dump(result, p)

        return result

    return wrapper


class Experiment(object):

    def __init__(self, id, version=0, cache=None):

        assert isinstance(id, str)
        assert isinstance(version, (int, float))

        self.id = id
        self.version = version
        self._trial_id = 0

        logger.info('{} is being initialized'.format(self))

        self._parameters = {}
        self._result = Undefined()

        # cache
        self._parameters_history = {}
        self._result_history = {}

        self.environment = Environment()
        self._metrics = MetricManager()

        if cache is None:
            dname = '{}_{}'.format(self.id, self.version)
            cache = pathlib.Path('cache') / dname
        self._cache = cache

        cache_dir = self.cache_dir
        if cache_dir.is_dir():
            msg = 'Use existing cache directory: {}'
            logger.info(msg.format(cache_dir.absolute()))
        elif cache_dir.is_file():
            msg = 'Unable to create cache directory, the same file exists: {}'
            raise FileExistsError(msg.format(cache_dir.absolute()))
        else:
            msg = 'Creating new cache directory: {}'
            logger.info(msg.format(cache_dir.absolute()))
            cache_dir.mkdir(parents=True)

    def __repr__(self):
        msg = 'Experiment(id: {}, version: {})'
        return msg.format(self.id, self.version)

    @property
    def cache_dir(self):
        return pathlib.Path(self._cache)

    def parameter(self, name):
        if name in self._parameters:
            msg = 'Parameter name must be unique in experiment: {}'
            raise ValueError(msg.format(name))

        self._parameters[name] = Undefined()
        # resolve_parameter returns a function to resolve parameter
        # otherwise parameter name collides in arg and dask_key_name
        return Parameter(self, name)

    def set_parameters(self, **kwargs):
        for key, value in kwargs.items():
            self._parameters[key] = value

        msg = 'Updated parameters: {}'
        logger.info(msg.format(self.show_parameters()))

    def get_parameters(self, trial_id):
        return self._parameters_history[trial_id]

    def show_parameters(self):
        def _format(k, v):
            # TODO: pretty print for long input
            if isinstance(v, Undefined):
                return '{}={}<{}>'.format(k, v, type(v))
            else:
                return '{}={}'.format(k, v)

        params = ['{}={}'.format(k, v)
                  for k, v in self._parameters.items()]
        return ', '.join(params)

    def __call__(self, func):
        return dask.delayed(func)

    ##########################################################
    # Decorators
    ##########################################################

    def persist(self, func):
        dask_obj = dask.delayed(persist_result(self, func))
        return dask_obj

    def result(self, func):
        dask_obj = dask.delayed(func)
        self._result = ResultLeaf(self, dask_obj)
        return self._result

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
        self.check_executable()

    def _finish_experiment_step(self, result):
        end_time = pd.Timestamp.now()
        record = {'Result': result, 'Finished': end_time,
                  'Process Time': end_time - self._start_time}
        self._result_history[self._trial_id] = record

        msg = 'Finished Experiment (trial id={})'
        logger.info(msg.format(self._trial_id))

    def check_executable(self):
        """ Check whether the current Experiment is executable.

        * Result is defined
        * Parameters are all defined
        """
        self._check_result_defined()
        self._check_parameters_defined()

    def _check_result_defined(self):
        if isinstance(self._result, Undefined):
            msg = ('Experiment result is not set. '
                   'Use Experiment.result decorator to define it')
            raise ParameterUndeclaredError(msg)

    def _check_parameters_defined(self):
        undefined = []
        for k, v in self._parameters.items():
            if isinstance(v, Undefined):
                undefined.append(k)

        if len(undefined) > 0:
            msg = ('Parameters are not defined. '
                   'Use Experiment.set_parameters to initialize: {}')
            raise ParameterUndefinedError(msg.format(', '.join(undefined)))

    ##########################################################
    # History management
    ##########################################################

    def get_history(self):
        parameters = pd.DataFrame.from_dict(self._parameters_history,
                                            orient='index')
        result_index = pd.Index(['Result', 'Finished', 'Process Time'])
        results = pd.DataFrame.from_dict(self._result_history,
                                         orient='index', columns=result_index)
        results = parameters.join(results)
        results.index.name = 'Trial ID'
        return results

    def get_persist_path(self, step, trial_id):
        fname = '{}_{}_{}_{}.pkl'.format(self.id, self.version, step, trial_id)
        return self.cache_dir / fname

    def get_persisted(self, step, trial_id):
        path = self.get_persist_path(step, trial_id)
        with path.open(mode='rb') as p:
            return pickle.load(p)

    ##########################################################
    # Metrics management
    ##########################################################

    def save_metric(self, key, epoch, value):
        self._metrics.save(key=key, trial_id=self._trial_id,
                           epoch=epoch, value=value)

    def load_metric(self, key, trial_id):
        return self._metrics.load(key=key, trial_id=trial_id)
