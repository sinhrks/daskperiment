import pytest

import pandas as pd

import daskperiment


class TrialManagerBase(object):

    @property
    def trials(self):
        raise NotImplementedError

    def test_lock(self):
        t = self.trials
        base = t.trial_id
        assert not t.is_locked()
        assert t.trial_id == base

        with pytest.raises(daskperiment.core.errors.TrialIDNotFoundError):
            t.current_trial_id

        i = t.increment()
        assert t.is_locked()
        assert i == base + 1
        assert t.current_trial_id == base + 1

        with pytest.raises(daskperiment.core.errors.LockedTrialError):
            t.trial_id

        with pytest.raises(daskperiment.core.errors.LockedTrialError):
            t.lock()

        with pytest.raises(daskperiment.core.errors.LockedTrialError):
            t.increment()

        t.unlock()
        assert not t.is_locked()
        assert t.trial_id == base + 1

        with pytest.raises(daskperiment.core.errors.TrialIDNotFoundError):
            t.current_trial_id

    def test_increment(self):
        t = self.trials
        base = t.trial_id
        assert t.trial_id == base

        res = t.increment()
        assert res == base + 1
        assert t.current_trial_id == base + 1
        t.unlock()
        assert t.trial_id == base + 1

        res = t.increment()
        assert res == base + 2
        assert t.current_trial_id == base + 2
        t.unlock()
        assert t.trial_id == base + 2

    def test_parameters(self):
        t = self.trials
        t.increment()
        trial_id = t.current_trial_id

        t.save_parameters(params=dict(a=1, b=1))
        t.unlock()

        res = t.increment()
        assert res == trial_id + 1

        t.save_parameters(params=dict(a=1, b='xx'))
        t.unlock()

        assert t.load_parameters(trial_id) == dict(a=1, b=1)
        assert t.load_parameters(trial_id + 1) == dict(a=1, b="xx")

    def test_parameters_types(self):
        t = self.trials
        t.increment()
        trial_id = t.current_trial_id

        params = dict(a=True, b=pd.Timestamp('2011-01-01'),
                      c=pd.Timedelta('1 days'))
        t.save_parameters(params=params)
        t.unlock()

        res = t.increment()
        assert res == trial_id + 1

        t.save_parameters(params=dict(a=1, b='xx'))

        assert t.load_parameters(trial_id) == params
        assert t.load_parameters(trial_id + 1) == dict(a=1, b="xx")

    def test_history_types(self):
        t = self.trials
        t.increment()
        trial_id = t.current_trial_id

        params = dict(a=True, b=pd.Timestamp('2011-01-01'),
                      c=pd.Timedelta('1 days'))
        t.save_history(params)
        t.unlock()

        res = t.increment()
        assert res == trial_id + 1

        t.save_history(dict(a=1, b='xx'))

        history = t.get_result_history()
        assert isinstance(history, dict), history
        assert history[trial_id] == params
        assert history[trial_id + 1] == dict(a=1, b="xx")

    def test_maybe_pure(self):
        t = self.trials

        def total(a=1, b=2, c=3):
            return a + b + c

        # correct result
        assert t.maybe_pure(total, ([1, 2, 3], {}), 6)
        assert t.maybe_pure(total, ([1, 2, 3], {}), 6)

        # pass different result value regards function as unpure
        assert not t.maybe_pure(total, ([1, 2, 3], {}), 5)
        # as the internal hash is changed, it regards a function as pure
        assert t.maybe_pure(total, ([1, 2, 3], {}), 5)
        assert not t.maybe_pure(total, ([1, 2, 3], {}), 6)

        # input is changed
        assert t.maybe_pure(total, ([1, 2], {'c': 3}), 5)
        assert t.maybe_pure(total, ([1, 2], {'c': 3}), 5)
        assert not t.maybe_pure(total, ([1, 2], {'c': 3}), 6)
