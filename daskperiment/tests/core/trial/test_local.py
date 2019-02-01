from daskperiment.core.trial import LocalTrialManager
from daskperiment.tests.core.trial.base import TrialManagerBase


class TestLocalTrialManager(TrialManagerBase):

    @property
    def trials(self):
        return LocalTrialManager('dummy')

    def test_init(self):
        # test trial_id is properly initialized
        t = LocalTrialManager('init')
        assert t.trial_id == 0
        assert not t.is_locked()
