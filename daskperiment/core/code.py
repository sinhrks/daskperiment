import inspect
import os

from daskperiment.util.diff import unified_diff
from daskperiment.util.log import get_logger


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

    def register(self, func):
        key = func.__name__
        source = inspect.getsource(func)
        # if key is found in ANY PREVIOUS experiments
        if key in self.history:
            if self.history[key] != source:
                msg = 'Code context has been changed: {}'
                logger.warn(msg.format(key))
                for d in unified_diff(self.history[key], source):
                    logger.warn(d)
        self.history[key] = source

        # if new key is being registered to CURRENT experiment
        if key not in self.codes:
            self.codes.append(key)

    def describe(self):
        codes = [self.history[key] for key in self.codes]
        return (os.linesep + os.linesep).join(codes)

    def save(self, trial_id, path):
        """
        Save code context from file
        """
        header = '# Code output saved in trial_id={}'.format(trial_id)
        self.history[trial_id] = path
        path.write_text(header + os.linesep + self.describe())

    def load(self, trial_id):
        """
        Load code context from file
        """
        codes = self.history[trial_id].read_text()
        # skip header
        codes = codes.split(os.linesep)[1:]
        return os.linesep.join(codes)
