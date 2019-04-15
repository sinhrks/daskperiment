from daskperiment.core.errors import LockedTrialError
from daskperiment.core.trial.base import _TrialManager
from daskperiment.util.log import get_logger


logger = get_logger(__name__)


class LocalTrialManager(_TrialManager):

    def __init__(self, backend):
        super().__init__(backend)
        self._trial_id = 0

        self._parameters_history = {}
        self._result_history = {}

        # store function input hash and its output hash
        self._hashes = {}

    @property
    def trial_id(self):
        """
        Return latest trial ID.
        """
        if self.is_locked():
            msg = ('Unable to use TrialManager.trial_id during trial. '
                   'Use .current_trial_id for safety.')
            raise LockedTrialError(msg)
        return self._trial_id

    def _increment(self):
        self._trial_id += 1
        return self._trial_id

    def _save_parameters(self, trial_id, params):
        self._parameters_history[trial_id] = params

    def load_parameters(self, trial_id):
        return self._parameters_history[trial_id]

    def _save_result(self, trial_id, params):
        self._result_history[trial_id] = params

    def get_parameter_history(self):
        return self._parameters_history.copy()

    def get_result_history(self):
        return self._result_history.copy()

    def _update_step_hash(self, key, output_hash):
        """
        Update the hash result of experiment step. Return previous hash
        if exists.
        """
        # return previous hash if exists, otherwise returns current
        previous_hash = self._hashes.get(key, output_hash)
        # overwrite with current hash
        self._hashes[key] = output_hash
        return previous_hash
