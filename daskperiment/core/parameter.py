from dask.delayed import Delayed

from daskperiment.core.errors import (ParameterUndeclaredError,
                                      ParameterUndefinedError)


class Undefined(object):

    def __repr__(self):
        return 'Undefined'


class Parameter(Delayed):
    __slots__ = ('_experiment', '_key', 'dask', '_length')

    def __init__(self, experiment, name, length=None):
        self._experiment = experiment

        self._key = name
        self.dask = {name: (self.resolve, )}
        self._length = length

    def __repr__(self):
        val = self._experiment._parameters[self._key]
        if isinstance(val, Undefined):
            return 'Parameter({}: {})'.format(self._key, val)
        else:
            return 'Parameter({}: {}{})'.format(self._key, val, type(val))

    def resolve(self):
        try:
            param = self._experiment._parameters[self._key]
            if isinstance(param, Undefined):
                msg = ('Parameter is not defined. '
                       'Use Experiment.set_parameters to initialize: {}')
                raise ParameterUndefinedError(msg.format(self._key))
            return param
        except KeyError:
            msg = ('Parameter is not declared. '
                   'Use Experiment.parameter to declare: {}')
            raise ParameterUndeclaredError(msg.format(self._key))
