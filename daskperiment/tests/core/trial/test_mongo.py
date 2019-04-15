from daskperiment.backend.mongo import MongoBackend
from daskperiment.testing import CleanupMixin
from daskperiment.tests.core.trial.base import TrialManagerBase


class TestMongoTrialManager(TrialManagerBase, CleanupMixin):

    backend = 'mongodb://localhost:27017/test_db'

    @property
    def trials(self):
        backend = MongoBackend('dummy', self.backend)
        return backend.get_trial_manager()

    def test_init(self):
        # test trial_id is properly initialized
        backend = MongoBackend('init', self.backend)
        t = backend.get_trial_manager()
        assert t.trial_id == 0
        assert not t.is_locked()
