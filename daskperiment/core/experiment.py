import functools

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

    def compute(self, seed=None, **kwargs):
        # increment trial id before experiment start
        exp = self._experiment
        exp._prepare_experiment_step()

        try:
            logger.info('Target: {}'.format(self._key))
            seed = exp.set_seed(seed)
            # save may raise errors
            exp._save_experiment_step()

            result = super().compute(**kwargs)
            exp._finish_experiment_step(result=result, success=True,
                                        description=np.nan, seed=seed)
            return result
        except Exception as e:
            description = '{}({})'.format(e.__class__.__name__, e)
            logger.error('Experiment failed: {}'.format(description))
            exp._finish_experiment_step(result=None, success=False,
                                        description=description, seed=seed)
            raise

    def _maybe_file(self):
        """
        Perform computation if experiment script is executed as file
        """
        if self._experiment._environment.maybe_file():
            seed, parameters = parse_command_arguments()
            self._experiment.set_parameters(**parameters)
            self.compute(seed=seed)


def wrap_result(experiment, func, persist=False):
    """
    Persist (cache) an intermediate step result
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)

        experiment._trials.maybe_pure(func, (args, kwargs), result)

        if persist:
            experiment._save_persist(func.__name__, result)
        return result

    return wrapper


class Experiment(object):

    _instance_cache = {}

    def __new__(cls, id, backend='local', seed=None):
        # return the identical instance based on id
        if id in cls._instance_cache:
            return cls._instance_cache[id]

        obj = super().__new__(cls)

        id = validate_key(id, keyname='Experiment ID')
        obj.id = id
        cls._instance_cache[id] = obj
        return obj

    def __init__(self, id, backend='local', seed=None):
        """
        Automatically load myself if cached pickle file exists
        """
        self._backend = init_backend(experiment_id=self.id,
                                     backend=backend)
        self._backend = self._backend.load()
        self._seed = seed

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
        msg = 'Experiment(id: {}, trial_id: {}, backend: {})'
        return msg.format(self.id, self.trial_id, self._backend)

    @property
    def trial_id(self):
        """
        Return latest trial ID of the experiment.

        If the trial is performed IMMEDIATELY after, the trial's ID should be
        the ID displayed here.

        In database-like backends, trial ID may be changed by other process.
        Thus, actual trial ID is fixed after the trial is started.
        """
        return self._trials.trial_id

    @property
    def current_trial_id(self):
        """
        Return current trial ID of the trial.

        It is accessible during the trial is performing, and specifies the ID
        which the trial is stored.
        """
        return self._trials.current_trial_id

    @property
    def _trials(self):
        """
        Property for TrialManager
        """
        return self._backend.trials

    @property
    def _metrics(self):
        """
        Property for MetricManager
        """
        return self._backend.metrics

    ##########################################################
    # Parameter
    ##########################################################

    def parameter(self, name, default=None):
        """
        Declare a parameter in the Experiment.

        It returns Parameter instance which can be passed as an argument to
        experiment functions.

        Prameters
        ---------
        name: str
           Parameter variable name in the Experiment.
           You must specify the name provided here in .set_parameters.
        default: object, optional
           Default value of the parameter.

        Returns
        -------
        Parameter: parameter
        """
        return self._parameters.define(name, default=default)

    def set_parameters(self, **kwargs):
        """
        Define (set) values to declared parameters.

        It is a method to combine parameter name and actual value for
        the trial.

        Prameters
        ---------
        **kwargs: dict
           Provide parameter name and values as key=value format, like
           .set_parameters(a=1, b=2)

        Returns
        -------
        None
        """
        self._parameters.set(**kwargs)

    def get_parameters(self, trial_id=None):
        """
        Get parameter values used in the trial.

        Prameters
        ---------
        trial_id: int, optional
           Trial ID to get parameters. If not provided, current paramters are
           returned.

        Returns
        -------
        dict: parameters
        """
        if trial_id is None:
            return self._parameters.to_dict()
        else:
            self._check_trial_id(trial_id)
            return self._trials.load_parameters(trial_id)

    def set_seed(self, seed=None):
        if seed is None:
            # use experiment default
            seed = self._seed

        if seed is None:
            # If seed is not provided, generate new seed
            seed = np.random.randint(2 ** 32 - 1)
            msg = ('Random seed is not provided, '
                   'initialized with generated seed: {}')
            logger.info(msg.format(seed))
        else:
            msg = ('Random seed is initialized with given seed: {}')
            logger.info(msg.format(seed))

        import random
        random.seed(seed)
        np.random.seed(seed)
        return seed

    ##########################################################
    # Save / load myself
    ##########################################################

    def _save(self):
        """
        Save current state to backend. This is automatically called when
        Result.compute() is called.
        """
        self._backend.save()

    def _delete_cache(self):
        """
        Delete cache dir. This should be only used in test functions.
        """
        self._backend._delete_cache()

    ##########################################################
    # Decorators
    ##########################################################

    def __call__(self, func):
        """
        A decorator to declare the function is in experiment step.

        It returns a ExperimentFunction which inherits Dask.Delayed.

        Prameters
        ---------
        func: callable
           A function for experiment step

        Returns
        -------
        ExperimentFunction: func
        """
        return self._build_step(func, persist=False)

    def persist(self, func):
        """
        A decorator to declare the function is in experiment step, and
        persists the function's results in each trials.

        It returns a ExperimentFunction which inherits Dask.Delayed.

        Prameters
        ---------
        func: callable
           A function for experiment step

        Returns
        -------
        ExperimentFunction: func
        """
        return self._build_step(func, persist=True)

    def _build_step(self, func, persist=False):
        """
        Build a single eperiment step
        """
        dask_obj = dask.delayed(wrap_result(self, func, persist=persist))
        self._codes.register(func)
        return ExperimentFunction(self, dask_obj)

    def result(self, func):
        """
        A decorator to declare the function is the last experiment step.

        It returns a ResultFunction which inherits Dask.Delayed.

        The difference from ExperimentFunction is that ResultFunction updates
        experimet's history, but ExperimentFunction doesn't.

        Prameters
        ---------
        func: callable
           A function for experiment step

        Returns
        -------
        ResultFunction: func
        """
        dask_obj = dask.delayed(wrap_result(self, func))
        self._codes.register(func)
        return ResultFunction(self, dask_obj)

    ##########################################################
    # Run experiment
    ##########################################################

    def _prepare_experiment_step(self):
        """
        Start a trial
        """
        # when myself is not executable, immediately raise
        # (do not store history)
        self.check_executable()

        # TODO: rethinking order
        self._trials.start_trial()

    def _save_experiment_step(self):
        """
        Save the trial info
        """
        trial_id = self._trials.current_trial_id
        self._trials.save_parameters(self._parameters)
        self._codes.save(trial_id)
        self._environment.save(trial_id)

    def _finish_experiment_step(self, result, success, description, seed):
        """
        Finish the trial
        """
        self._trials.finish_trial(result=result, success=success,
                                  description=description, seed=seed)
        self._save()

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
        """
        Return a trial history of the experiment.

        It stores trial parameters and its results and related information.

        Returns
        -------
        DataFrame: history
        """
        return self._trials.get_history()

    def _save_persist(self, step, result):
        trial_id = self._trials.current_trial_id
        key = self._backend.get_persist_key(step, trial_id)
        self._backend.save_object(key, result)

    def get_persisted(self, step, trial_id):
        """
        Get persisted result.

        Prameters
        ---------
        step: str
           The name of the function decorated by persist.
        trial_id: int
           Trial ID to be loaded

        Returns
        -------
        object: persisted_result
        """
        self._check_trial_id(trial_id)

        key = self._backend.get_persist_key(step, trial_id)
        return self._backend.load_object(key)

    ##########################################################
    # Code management
    ##########################################################

    def get_code(self, trial_id=None):
        """
        Get code context in the trial.

        Prameters
        ---------
        trial_id: int, optional
           Trial ID to get code context. If not provided, current code
           context is returned.

        Returns
        -------
        str: code_context
        """
        if trial_id is not None:
            self._check_trial_id(trial_id)
        return self._codes.get_code(trial_id=trial_id)

    ##########################################################
    # Metrics management
    ##########################################################

    def save_metric(self, metric_key, epoch, value):
        """
        Save metric during the trial (a transition of values during the trial).

        Prameters
        ---------
        metric_key: str
           A key to distinguish metric
        epoch: int
           An epoch when the metric is recorded
        value: scalar
           A value of the distinguish metric
        """
        trial_id = self._trials.current_trial_id
        self._metrics.save(metric_key=metric_key, trial_id=trial_id,
                           epoch=epoch, value=value)

    def load_metric(self, metric_key, trial_id):
        """
        Load metric during the trial (a transition of values during the trial).

        Prameters
        ---------
        metric_key: str
           A key to distinguish metric
        trial_id: int, list of int
           Trial ID(s) to load metric.

        Returns
        -------
        DataFrame: metrics
        """
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
            # Code change shouldn't be checked here,
            # codes are registered after instanciation
            # self._codes.check_code_change(trial_id)

            self._environment.check_environment_change(trial_id)
            self._environment.check_python_packages_change(trial_id)

    def get_environment(self, trial_id=None):
        """
        Get environment info in the trial.

        * Platform information
        * Python information
        * daskperiment information

        Prameters
        ---------
        trial_id: int, optional
           Trial ID to get environment information. If not provided, current
           environment information is returned.

        Returns
        -------
        list of str: environment
        """
        if trial_id is not None:
            self._check_trial_id(trial_id)
        return self._environment.get_environment(trial_id=trial_id)

    def get_python_packages(self, trial_id=None):
        """
        Get installed Python package information in the trial.

        The format is the same as pip freeze.

        Prameters
        ---------
        trial_id: int, optional
           Trial ID to get code context. If not provided, current code
           context is returned.

        Returns
        -------
        list of str: packages
        """
        if trial_id is not None:
            self._check_trial_id(trial_id)
        return self._environment.get_python_packages(trial_id=trial_id)

    ##########################################################
    # Dashboard
    ##########################################################

    def start_dashboard(self, port=5000):
        """
        Start DaskperimentBoard web application.
        """
        import daskperiment.board.board as board
        return board.maybe_start_dashboard(self, port=port)
