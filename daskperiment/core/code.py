import inspect
import os

from daskperiment.util.log import get_logger


logger = get_logger(__name__)


class CodeManager(object):

    def __init__(self, *args):
        self._codes = list(args)

    def copy(self):
        return CodeManager(*self._codes)

    def register(self, func):
        self._codes.append(inspect.getsource(func))

    def describe(self):
        return (os.linesep + os.linesep).join(self._codes)
