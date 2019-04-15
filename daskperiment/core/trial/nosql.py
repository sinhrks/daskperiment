from daskperiment.core.errors import (LockedTrialError,
                                      TrialIDNotFoundError)
from daskperiment.core.trial.base import _TrialManager
from daskperiment.util.log import get_logger
from daskperiment.core.parameter import Undefined


logger = get_logger(__name__)


class _NoSQLTrialManager(_TrialManager):

    @property
    def experiment_id(self):
        return self.backend.experiment_id

    @property
    def _trial_id_key(self):
        return self.backend._get_trial_id_key()

    @property
    def trial_id(self):
        """
        Return latest trial ID.
        """
        if self.is_locked():
            msg = ('Unable to use TrialManager.trial_id during trial. '
                   'Use .current_trial_id for safety.')
            raise LockedTrialError(msg)
        res = self.backend.get(self._trial_id_key)
        if res is None:
            return 0
        else:
            return int(res)

    def _increment(self):
        return self.backend.increment(self._trial_id_key)

    def _save_parameters(self, trial_id, params):
        # TODO : how to distinguish Undefined and nan?
        params = {k: v for k, v in params.items()
                  if not isinstance(v, Undefined)}
        key = self.backend.get_parameter_key(trial_id)
        self.backend.save_object(key, params)

    def load_parameters(self, trial_id):
        key = self.backend.get_parameter_key(trial_id)
        return self.backend.load_object(key)

    def _save_result(self, trial_id, params):
        key = self.backend.get_history_key(trial_id)
        self.backend.save_object(key, params)

    def get_parameter_history(self):
        return self._get_parameter_history()

    def get_result_history(self):
        return self._get_result_history()

    def _update_step_hash(self, input_hash, output_hash):
        """
        Update the hash result of experiment step. Return previous hash
        if exists.
        """
        # include experiment_id in key
        key = self.backend.get_step_hash_key(input_hash)
        # return previous hash if exists, otherwise returns current
        try:
            previous_output_hash = self.backend.load_text(key)
        except TrialIDNotFoundError:
            # it doesn't use trial id...
            previous_output_hash = output_hash
        # overwrite with current hash
        self.backend.save_text(key, output_hash)
        return previous_output_hash


class RedisTrialManager(_NoSQLTrialManager):

    def _get_parameter_history(self):
        query = self.backend.get_parameter_key('*')
        keys = self.backend.keys(query)
        k = self.backend.get_trial_id_from_key
        return {k(key): self.backend.load_object(key) for key in keys}

    def _get_result_history(self):
        query = self.backend.get_history_key('*')
        keys = self.backend.keys(query)
        k = self.backend.get_trial_id_from_key
        return {k(key): self.backend.load_object(key) for key in keys}


class MongoTrialManager(_NoSQLTrialManager):
    def _get_parameter_history(self):
        query = self.backend.get_parameter_key('*')
        return self._find_previous_trials(query)

    def _get_result_history(self):
        query = self.backend.get_history_key('*')
        return self._find_previous_trials(query)

    def _find_previous_trials(self, query):
        self.backend._validate_key(query)
        docs = self.backend.collection.find(query.document_meta)

        results = {}
        for doc in docs:
            try:
                obj = self.backend.loads_object(doc[query.field_name])
                results[doc['trial_id']] = obj
            except KeyError:
                pass
        return results
