from dask.base import tokenize
from dask.delayed import Delayed

from daskperiment.core.errors import (ParameterUndeclaredError,
                                      ParameterUndefinedError)
from daskperiment.util.log import get_logger


logger = get_logger(__name__)


class Undefined(object):

    def __repr__(self):
        return 'Undefined'

    def __eq__(self, other):
        if isinstance(other, Undefined):
            return True
        else:
            return False


class Parameter(Delayed):
    __slots__ = ('_experiment', '_name', '_key', 'dask', '_length')

    def __init__(self, experiment, name, length=None):
        self._experiment = experiment

        # parameter representation name, like "a"
        self._name = name
        # parameter with token, like "a-xxxx"
        self._key = name + "-" + tokenize(name)
        self.dask = {self._key: (self.resolve, )}
        self._length = length

    def __repr__(self):
        val = self._experiment._parameters[self._name]
        if isinstance(val, Undefined):
            return 'Parameter({}: {})'.format(self._name, val)
        else:
            return 'Parameter({}: {}{})'.format(self._name, val, type(val))

    def resolve(self):
        try:
            param = self._experiment._parameters[self._name]
            if isinstance(param, Undefined):
                raise ParameterUndefinedError(self._name)
            return param
        except KeyError:
            raise ParameterUndeclaredError(self._name)


class ParameterManager(object):

    def __init__(self, **kwargs):
        self._parameters = kwargs

    def copy(self):
        return ParameterManager(**self._parameters)

    def describe(self):
        def _format(k, v):
            # TODO: pretty print for long input
            if not isinstance(v, Undefined):
                return '{}={}{}'.format(k, v, type(v))
            else:
                return '{}={}'.format(k, v)

        params = [_format(k, v)
                  for k, v in self._parameters.items()]
        return ', '.join(params)

    def to_dict(self):
        return dict(self._parameters)

    def define(self, name, default=None):
        """"
        Declare parameter
        """
        if name in self._parameters:
            msg = 'Re-defining existing parameter: {}'
            logger.debug(msg.format(name))
        else:
            if default is None:
                self._parameters[name] = Undefined()
            else:
                self._parameters[name] = default
        # resolve_parameter returns a function to resolve parameter
        # otherwise parameter name collides in arg and dask_key_name
        return Parameter(self, name)

    def set(self, **kwargs):
        """"
        Define parameter (set parameter value)
        """
        for name, value in kwargs.items():
            if name in self._parameters:
                self._parameters[name] = value
            else:
                raise ParameterUndeclaredError(name)

        msg = 'Updated parameters: {}'
        logger.info(msg.format(self.describe()))

    def _check_all_defined(self):
        undefined = []
        for k, v in self._parameters.items():
            if isinstance(v, Undefined):
                undefined.append(k)

        if len(undefined) > 0:
            raise ParameterUndefinedError(', '.join(undefined))
