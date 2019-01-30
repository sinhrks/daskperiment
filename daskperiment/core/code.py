import inspect
import os

from daskperiment.util.diff import unified_diff
from daskperiment.util.log import get_logger
from daskperiment.util.text import trim_indent


logger = get_logger(__name__)


class CodeManager(object):

    def __init__(self, codes=None, history=None):
        # Track registered code's key in CURRENT Experiment
        # (do not care for cached result, not pickled)
        if codes is None:
            self.codes = []
        else:
            self.codes = codes

        # Track registered code's key and context in ALL PREVIOUS Experiments
        if history is None:
            self.history = {}
        else:
            self.history = history

    def __getstate__(self):
        state = {}
        # Do not pickle self.codes because it is overwritten after load
        state['history'] = self.history
        return state

    def __setstate__(self, state):
        self.codes = []
        self.history = state['history']

    def copy(self):
        return CodeManager(codes=self.codes,
                           history=self.history)

    def _get_code_context(self, func):
        try:
            source = inspect.getsource(func)
            source = trim_indent(source)
            return source
        except Exception:
            msg = 'Unable to get code context: '
            logger.warning(msg.format(func.__name__))
            return ''

    def register(self, func):
        """
        Register function's code context
        """
        key = func.__name__
        source = self._get_code_context(func)

        # if key is found in ANY PREVIOUS experiments
        if key in self.history:
            if self.history[key] != source:
                msg = 'Code context has been changed: {}'
                logger.warning(msg.format(key))
                for d in unified_diff(self.history[key], source):
                    logger.warning(d)
        self.history[key] = source

        # if new key is being registered to CURRENT experiment
        if key not in self.codes:
            self.codes.append(key)

    def describe(self):
        """
        Describe current code context
        """
        codes = [self.history[key] for key in self.codes]
        return (os.linesep + os.linesep).join(codes)
