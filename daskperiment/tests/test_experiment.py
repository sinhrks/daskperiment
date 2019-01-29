import pytest

import numpy as np
import pandas as pd
import pandas.testing as tm

import daskperiment
from daskperiment.core.errors import TrialIDNotFoundError


def assert_history_equal(df, exp):
    tm.assert_index_equal(df.columns[-5:],
                          pd.Index(['Result', 'Success', 'Finished',
                                    'Process Time', 'Description']))
    tm.assert_frame_equal(df.drop(['Finished', 'Process Time'], axis=1),
                          exp)


class TestExperiment(object):

    def test_is(self):
        ex1 = daskperiment.Experiment(id="test_parameter")
        ex2 = daskperiment.Experiment(id="test_parameter")
        assert ex1 is ex2

    def test_repr(self):
        ex = daskperiment.Experiment(id="test_repr")
        assert repr(ex) == 'Experiment(id: test_repr, trial_id: 0)'

        a = ex.parameter('a')

        @ex.result
        def inc(a):
            return a + 1

        res = inc(a)
        ex.set_parameters(a=1)
        assert res.compute() == 2

        assert repr(ex) == 'Experiment(id: test_repr, trial_id: 1)'

        ex._delete_cache()

    def test_compute(self):
        ex = daskperiment.Experiment(id="test_parameter")
        a = ex.parameter("a")

        @ex.result
        def inc(a):
            return a + 1

        res = inc(a)

        ex.set_parameters(a=1)
        assert res.compute() == 2

        ex.set_parameters(a=3)
        assert res.compute() == 4

        hist = ex.get_history()
        exp = pd.DataFrame({'a': [1, 3],
                            'Result': [2, 4],
                            'Success': [True, True],
                            'Description': [np.nan, np.nan]},
                           index=pd.Index([1, 2], name='Trial ID'),
                           columns=['a', 'Result', 'Success', 'Description'])
        assert_history_equal(hist, exp)

        ex._delete_cache()

    def test_pattern(self):
        ex = daskperiment.Experiment(id="test_pattern")
        a = ex.parameter("a")

        def inc(a):
            # no decorated function
            return a + 1

        @ex.result
        def add(a, b):
            return a + b

        res = add(inc(a), a + 3)

        ex.set_parameters(a=1)
        assert res.compute() == 6

        ex.set_parameters(a=3)
        assert res.compute() == 10

        hist = ex.get_history()
        exp = pd.DataFrame({'a': [1, 3],
                            'Result': [6, 10],
                            'Success': [True, True],
                            'Description': [np.nan, np.nan]},
                           index=pd.Index([1, 2], name='Trial ID'),
                           columns=['a', 'Result', 'Success', 'Description'])
        assert_history_equal(hist, exp)

        ex._delete_cache()

    def test_persist(self):
        ex = daskperiment.Experiment(id="test_persist")
        a = ex.parameter("a")

        @ex.persist
        def inc(a):
            return a + 1

        @ex.result
        def add(a, b):
            return a + b

        res = add(inc(a), a)

        ex.set_parameters(a=1)
        assert res.compute() == 3

        ex.set_parameters(a=3)
        assert res.compute() == 7

        assert ex.get_persisted('inc', trial_id=1) == 2
        assert ex.get_persisted('inc', trial_id=2) == 4

        hist = ex.get_history()
        exp = pd.DataFrame({'a': [1, 3],
                            'Result': [3, 7],
                            'Success': [True, True],
                            'Description': [np.nan, np.nan]},
                           index=pd.Index([1, 2], name='Trial ID'),
                           columns=['a', 'Result', 'Success', 'Description'])
        assert_history_equal(hist, exp)

        ex._delete_cache()

    def test_failure(self):
        ex = daskperiment.Experiment(id="test_failure")
        a = ex.parameter("a")

        @ex.result
        def div(a):
            return 3 / a

        res = div(a)

        ex.set_parameters(a=1)
        assert res.compute() == 3

        ex.set_parameters(a=2)
        assert res.compute() == 1.5

        ex.set_parameters(a=0)
        with pytest.raises(ZeroDivisionError):
            res.compute()

        hist = ex.get_history()
        exp_err = 'ZeroDivisionError(division by zero)'
        exp = pd.DataFrame({'a': [1, 2, 0],
                            'Result': [3.0, 1.5, np.nan],
                            'Success': [True, True, False],
                            'Description': [np.nan, np.nan, exp_err]},
                           index=pd.Index([1, 2, 3], name='Trial ID'),
                           columns=['a', 'Result', 'Success', 'Description'])
        assert_history_equal(hist, exp)

        ex._delete_cache()

    def test_dup_param(self):
        ex = daskperiment.Experiment(id="test_dup_param")
        a = ex.parameter("a")

        @ex.result
        def concat(a, b):
            return str(a) + b

        # variable a is a parameter, str "a" isn't
        res = concat(a, "a")

        ex.set_parameters(a=1)
        assert res.compute() == "1a"

        ex.set_parameters(a="a")
        assert res.compute() == "aa"

        ex._delete_cache()

    def test_invalid_trial_id(self):
        ex = daskperiment.Experiment(id="test_invalid_trial")
        a = ex.parameter("a")

        @ex.persist
        def inc(a):
            return a + 1

        @ex.result
        def add(a, b):
            return a + b

        res = add(inc(a), a)

        ex.set_parameters(a=1)
        assert res.compute() == 3

        match = 'Unable to find trial id:'
        with pytest.raises(TrialIDNotFoundError, match=match):
            ex.get_parameters(trial_id=0)
        with pytest.raises(TrialIDNotFoundError, match=match):
            ex.get_parameters(trial_id=2)
        assert ex.get_parameters(trial_id=1) == dict(a=1)

        with pytest.raises(TrialIDNotFoundError, match=match):
            ex.get_persisted('inc', trial_id=0)
        with pytest.raises(TrialIDNotFoundError, match=match):
            ex.get_persisted('inc', trial_id=2)
        assert ex.get_persisted('inc', trial_id=1) == 2

        ex._delete_cache()

    def test_autoload(self):
        ex = daskperiment.Experiment(id="test_autoload")
        a = ex.parameter("a")
        trial_id = ex._trial_id

        @ex.result
        def inc(a):
            return a + 1

        res = inc(a)

        ex.set_parameters(a=1)
        assert res.compute() == 2

        ex.set_parameters(a=3)
        assert res.compute() == 4

        assert ex._trial_id == trial_id + 2
        ex2 = daskperiment.Experiment(id="test_autoload")
        assert ex is ex2
        assert ex2._trial_id == trial_id + 2

        # DO NOT DELETE CACHE to test auto-loaded instance
        # ex._delete_cache()

    def test_metric(self):
        ex = daskperiment.Experiment(id="test_metric")
        a = ex.parameter('a')
        assert ex._trial_id == 0

        @ex.result
        def inc(a):
            ex.save_metric('dummy_metric', epoch=1, value=2)
            ex.save_metric('dummy_metric', epoch=2, value=4)
            return a + 1

        res = inc(a)
        ex.set_parameters(a=3)
        assert res.compute() == 4
        assert ex._trial_id == 1

        res = ex.load_metric('dummy_metric', trial_id=[1])
        exp_idx = pd.Index([1, 2], name='Epoch')
        exp_columns = pd.Index([1], name='Trial ID')
        exp = pd.DataFrame({1: [2, 4]}, index=exp_idx, columns=exp_columns)
        tm.assert_frame_equal(res, exp)

        @ex.result
        def dummy():
            ex.save_metric('dummy_metric2', epoch=1, value=5)
            return 0

        res = dummy()
        res.compute()
        assert ex._trial_id == 2

        res = ex.load_metric('dummy_metric2', trial_id=[2])
        exp_idx = pd.Index([1], name='Epoch')
        exp_columns = pd.Index([2], name='Trial ID')
        exp = pd.DataFrame({2: [5]}, index=exp_idx, columns=exp_columns)
        tm.assert_frame_equal(res, exp)

        res = inc(a)
        ex.set_parameters(a=4)
        assert res.compute() == 5
        assert ex._trial_id == 3

        res = ex.load_metric('dummy_metric', trial_id=[1, 3])
        exp_idx = pd.Index([1, 2], name='Epoch')
        exp_columns = pd.Index([1, 3], name='Trial ID')
        exp = pd.DataFrame({1: [2, 4], 3: [2, 4]},
                           index=exp_idx, columns=exp_columns)
        tm.assert_frame_equal(res, exp)

        ex._delete_cache()

    def test_metric_invalid_trial_id(self):
        ex = daskperiment.Experiment(id="test_metric_invalid")
        a = ex.parameter('a')
        assert ex._trial_id == 0

        @ex.result
        def inc(a):
            ex.save_metric('dummy_metric', epoch=1, value=2)
            ex.save_metric('dummy_metric', epoch=2, value=4)
            return a + 1

        res = inc(a)
        ex.set_parameters(a=3)
        assert res.compute() == 4
        assert ex._trial_id == 1

        match = 'Unable to find trial id:'
        with pytest.raises(TrialIDNotFoundError, match=match):
            ex.load_metric('dummy_metric', trial_id=0)
        with pytest.raises(TrialIDNotFoundError, match=match):
            ex.load_metric('dummy_metric', trial_id=2)

        res = ex.load_metric('dummy_metric', trial_id=1)
        exp_idx = pd.Index([1, 2], name='Epoch')
        exp_columns = pd.Index([1], name='Trial ID')
        exp = pd.DataFrame({1: [2, 4]},
                           index=exp_idx, columns=exp_columns)
        tm.assert_frame_equal(res, exp)

        with pytest.raises(ValueError, match='Unable to find saved metric:'):
            ex.load_metric('invalid_metric', trial_id=1)

        @ex.result
        def inc(a):
            return a + 1

        res = inc(a)
        ex.set_parameters(a=4)
        assert res.compute() == 5
        assert ex._trial_id == 2

        with pytest.raises(TrialIDNotFoundError, match=match):
            ex.load_metric('dummy_metric', trial_id=2)

        ex._delete_cache()

    def test_code(self):
        ex = daskperiment.Experiment(id="test_code")
        a = ex.parameter("a")

        @ex
        def inc(a):
            return a + 1

        @ex.result
        def add(a, b):
            return a + b

        res = add(inc(a), a)

        exp = """        @ex
        def inc(a):
            return a + 1


        @ex.result
        def add(a, b):
            return a + b
"""
        assert ex.get_code() == exp

        ex.set_parameters(a=3)
        assert res.compute() == 7
        assert ex.get_code(trial_id=1) == exp

        match = 'Unable to find trial id:'
        with pytest.raises(TrialIDNotFoundError, match=match):
            ex.get_code(trial_id=0)
        with pytest.raises(TrialIDNotFoundError, match=match):
            ex.get_code(trial_id=2)

        ex._delete_cache()

    def test_code_persist(self):
        ex = daskperiment.Experiment(id="test_code_persist")
        a = ex.parameter("a")

        @ex.persist
        def inc(a):
            return a + 1

        @ex.result
        def add(a, b):
            return a + b

        res = add(inc(a), a)

        exp = """        @ex.persist
        def inc(a):
            return a + 1


        @ex.result
        def add(a, b):
            return a + b
"""
        assert ex.get_code() == exp

        ex.set_parameters(a=3)
        assert res.compute() == 7
        assert ex.get_code(trial_id=1) == exp

        ex._delete_cache()
