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
    __slots__ = ('_name', '_key', 'dask', '_length', '_value')

    def __init__(self, name, length=None):
        # parameter representation name, like "a"
        self._name = name
        # parameter with token, like "a-xxxx"
        self._key = name + "-" + tokenize(name)

        # for Parameter.compute()
        self.dask = {self._key: (self.resolve, )}

        self._length = length
        self._value = Undefined()

    def __repr__(self):
        if self.is_undefined:
            typ = ''
        else:
            typ = type(self._value)

        return 'Parameter({}: {}{})'.format(self._name, self._value, typ)

    def summarize(self):
        """
        Return name=value format str
        """
        if self.is_undefined:
            typ = ''
        else:
            typ = type(self._value)

        return '{}={}{}'.format(self._name, self._value, typ)

    def set(self, value):
        """
        Set value to myself
        """
        self._value = value

    @property
    def is_undefined(self):
        return isinstance(self._value, Undefined)

    def resolve(self, allow_undefined=False):
        if not allow_undefined and self.is_undefined:
            raise ParameterUndefinedError(self._name)
        return self._value


class ParameterManager(object):

    def __init__(self):
        self._parameters = {}

    def describe(self):
        # TODO: pretty print for long input
        params = [p.summarize() for p in self._parameters.values()]
        return ', '.join(params)

    def to_dict(self):
        """
        Return dict of parameter name and its value
        """
        return {k: v.resolve(allow_undefined=True)
                for k, v in self._parameters.items()}

    def to_dask_dict(self):
        """
        Return dict to update dask graph
        """
        return {v._key: v.resolve() for v in self._parameters.values()}

    def define(self, name, default=None):
        """"
        Declare parameter
        """
        if name in self._parameters:
            msg = 'Re-defining existing parameter: {}'
            logger.debug(msg.format(name))
            return self._parameters[name]
        else:
            p = Parameter(name)
            if default is not None:
                p.set(default)
            self._parameters[name] = p
        return p

    def set(self, **kwargs):
        """"
        Define parameter (set parameter value)
        """
        for name, value in kwargs.items():
            if name in self._parameters:
                self._parameters[name].set(value)
            else:
                raise ParameterUndeclaredError(name)

        msg = 'Updated parameters: {}'
        logger.info(msg.format(self.describe()))

    def _check_all_defined(self):
        undefined = []
        for k, p in self._parameters.items():
            if p.is_undefined:
                undefined.append(k)

        if len(undefined) > 0:
            raise ParameterUndefinedError(', '.join(undefined))
