import inspect
import os

from daskperiment.backend import init_backend
from daskperiment.util.diff import unified_diff
from daskperiment.util.log import get_logger
from daskperiment.util.text import trim_indent


logger = get_logger(__name__)


class CodeManager(object):

    def __init__(self, backend):
        self.backend = init_backend(backend=backend)

        # Track registered code's key in CURRENT Experiment
        self.codes = []

        # Track registered code's key and context in ALL PREVIOUS Experiments
        self.history = {}

    def __getstate__(self):
        state = {}
        # Do not pickle self.codes because it is overwritten after load
        state['history'] = self.history
        return state

    def __setstate__(self, state):
        self.codes = []
        self.history = state['history']

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
            self._output_difference(self.history[key], source, key=key)
        self.history[key] = source

        # if new key is being registered to CURRENT experiment
        if key not in self.codes:
            self.codes.append(key)

    def _output_difference(self, previous, current, key=None):
        if previous != current:
            if key is None:
                msg = 'Code context has been changed'
                logger.warning(msg)
            else:
                msg = 'Code context has been changed: {}'
                logger.warning(msg.format(key))

            for d in unified_diff(previous, current):
                logger.warning(d)

    def get_code(self, trial_id=None):
        if trial_id is None:
            return self.describe()
        else:
            return self.load(trial_id)

    def describe(self):
        """
        Describe current code context
        """
        codes = [self.history[key] for key in self.codes]
        return (os.linesep + os.linesep).join(codes)

    def save(self, trial_id):
        key = self.backend.get_code_key(trial_id)
        msg = 'Saving code context: {}'
        logger.info(msg.format(key))

        code_context = self.describe()
        header = '# Code output saved in trial_id={}'.format(trial_id)
        code_context = header + os.linesep + code_context

        self.backend.save_text(key, code_context)

    def load(self, trial_id):
        key = self.backend.get_code_key(trial_id)
        code_context = self.backend.load_text(key)

        # skip header
        codes = code_context.splitlines()[1:]
        return os.linesep.join(codes) + os.linesep

    def check_code_change(self, trial_id):
        current = self.get_code()
        previous = self.get_code(trial_id=trial_id)
        self._output_difference(previous, current)
