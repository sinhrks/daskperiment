import pytest

import random

import numpy as np
import pandas as pd
import pandas.testing as tm

import daskperiment
from daskperiment.backend import LocalBackend
from daskperiment.core.errors import LockedTrialError, TrialIDNotFoundError


def assert_history_equal(df, exp):
    exp_index = ['Seed', 'Result', 'Result Type', 'Success', 'Finished',
                 'Process Time', 'Description']
    tm.assert_index_equal(df.columns[-len(exp_index):], pd.Index(exp_index))
    tm.assert_frame_equal(df.drop(['Seed', 'Finished', 'Process Time'],
                                  axis=1),
                          exp)


class ExperimentBase(object):

    @property
    def backend(self):
        raise NotImplementedError

    def test_is(self):
        ex1 = daskperiment.Experiment(id="test_parameter",
                                      backend=self.backend)
        ex2 = daskperiment.Experiment(id="test_parameter",
                                      backend=self.backend)
        assert ex1 is ex2

    def test_invalid_id(self):
        msg = 'Experiment ID must be str, given:'
        with pytest.raises(ValueError, match=msg):
            daskperiment.Experiment(id=1, backend=self.backend)

        msg = 'Experiment ID cannot contain colon '
        with pytest.raises(ValueError, match=msg):
            daskperiment.Experiment(id="aa:aa", backend=self.backend)

    def test_repr(self):
        ex = daskperiment.Experiment(id="test_repr", backend=self.backend)
        fmt = 'Experiment(id: test_repr, trial_id: {}, backend: {})'

        assert repr(ex) == fmt.format(0, ex._backend), repr(ex)

        a = ex.parameter('a')

        @ex.result
        def inc(a):
            return a + 1

        res = inc(a)
        ex.set_parameters(a=1)
        assert res.compute() == 2

        assert repr(ex) == fmt.format(1, ex._backend)

        ex._delete_cache()

    def test_parameter_undeclared(self):
        ex = daskperiment.Experiment(id="test_undeclared_param",
                                     backend=self.backend)
        with pytest.raises(daskperiment.core.errors.ParameterUndeclaredError,
                           match='Parameter is not declared'):
            ex.set_parameters(a=1)

        ex._delete_cache()

    def test_parameter_undefined(self):
        ex = daskperiment.Experiment(id="test_undefined_param",
                                     backend=self.backend)
        a = ex.parameter('a')

        @ex.result
        def inc(a):
            return a + 1

        res = inc(a)

        with pytest.raises(daskperiment.core.errors.ParameterUndefinedError,
                           match='Parameters are not defined'):
            res.compute()

        ex._delete_cache()

    def test_parameter_default(self):
        ex = daskperiment.Experiment(id="test_undefined_param",
                                     backend=self.backend)
        a = ex.parameter('a', default=2)
        assert a.compute() == 2

        @ex.result
        def inc(a):
            return a + 1

        res = inc(a)

        assert res.compute() == 3

        ex.set_parameters(a=3)
        assert res.compute() == 4

        ex._delete_cache()

    def test_compute(self):
        ex = daskperiment.Experiment(id="test_parameter",
                                     backend=self.backend)
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
                            'Result Type': ["<class 'int'>"] * 2,
                            'Success': [True, True],
                            'Description': [np.nan, np.nan]},
                           index=pd.Index([1, 2], name='Trial ID'),
                           columns=['a', 'Result', 'Result Type',
                                    'Success', 'Description'])
        assert_history_equal(hist, exp)

        ex._delete_cache()

    def test_pattern(self):
        ex = daskperiment.Experiment(id="test_pattern", backend=self.backend)
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
                            'Result Type': ["<class 'int'>"] * 2,
                            'Success': [True, True],
                            'Description': [np.nan, np.nan]},
                           index=pd.Index([1, 2], name='Trial ID'),
                           columns=['a', 'Result', 'Result Type',
                                    'Success', 'Description'])
        assert_history_equal(hist, exp)

        ex._delete_cache()

    def test_no_parameters(self):
        ex = daskperiment.Experiment(id="test_no_parameter",
                                     backend=self.backend)

        @ex.result
        def comp():
            return 1

        res = comp()

        assert res.compute() == 1
        assert res.compute() == 1

        hist = ex.get_history()
        exp = pd.DataFrame({'Result': [1, 1],
                            'Result Type': ["<class 'int'>"] * 2,
                            'Success': [True, True],
                            'Description': [np.nan, np.nan]},
                           index=pd.Index([1, 2], name='Trial ID'),
                           columns=['Result', 'Result Type',
                                    'Success', 'Description'])
        assert_history_equal(hist, exp)

        ex._delete_cache()

    def test_persist(self):
        ex = daskperiment.Experiment(id="test_persist", backend=self.backend)
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
                            'Result Type': ["<class 'int'>"] * 2,
                            'Success': [True, True],
                            'Description': [np.nan, np.nan]},
                           index=pd.Index([1, 2], name='Trial ID'),
                           columns=['a', 'Result', 'Result Type',
                                    'Success', 'Description'])
        assert_history_equal(hist, exp)

        ex._delete_cache()

    def test_failure(self):
        ex = daskperiment.Experiment(id="test_failure", backend=self.backend)
        a = ex.parameter("a")

        @ex.result
        def div(a):
            return 3 / a

        res = div(a)

        ex.set_parameters(a=1)
        assert res.compute() == 3
        assert ex.get_parameters() == dict(a=1)

        ex.set_parameters(a=2)
        assert res.compute() == 1.5
        assert ex.get_parameters() == dict(a=2)
        assert ex.get_parameters(1) == dict(a=1)
        assert ex.get_parameters(2) == dict(a=2)

        ex.set_parameters(a=0)
        with pytest.raises(ZeroDivisionError):
            res.compute()
        assert ex.get_parameters() == dict(a=0)
        assert ex.get_parameters(1) == dict(a=1)
        assert ex.get_parameters(2) == dict(a=2)
        assert ex.get_parameters(1) == dict(a=1)
        assert ex.get_parameters(3) == dict(a=0)

        hist = ex.get_history()
        exp_err = 'ZeroDivisionError(division by zero)'
        exp = pd.DataFrame({'a': [1, 2, 0],
                            'Result': [3.0, 1.5, np.nan],
                            'Result Type': ["<class 'float'>",
                                            "<class 'float'>",
                                            "None"],
                            'Success': [True, True, False],
                            'Description': [np.nan, np.nan, exp_err]},
                           index=pd.Index([1, 2, 3], name='Trial ID'),
                           columns=['a', 'Result', 'Result Type',
                                    'Success', 'Description'])
        assert_history_equal(hist, exp)

        ex._delete_cache()

    def test_dup_param(self):
        ex = daskperiment.Experiment(id="test_dup_param", backend=self.backend)
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
        ex = daskperiment.Experiment(id="test_invalid_trial",
                                     backend=self.backend)
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

    def test_current_trial_id(self):
        ex = daskperiment.Experiment(id="test_current_trial_id",
                                     backend=self.backend)

        @ex.result
        def comp():
            # trial_id is unaccessible in the trial
            with pytest.raises(LockedTrialError):
                ex.trial_id
            return ex.current_trial_id + 1

        res = comp()

        assert res.compute() == 2
        assert res.compute() == 3

        hist = ex.get_history()
        exp = pd.DataFrame({'Result': [2, 3],
                            'Result Type': ["<class 'int'>"] * 2,
                            'Success': [True, True],
                            'Description': [np.nan, np.nan]},
                           index=pd.Index([1, 2], name='Trial ID'),
                           columns=['Result', 'Result Type',
                                    'Success', 'Description'])
        assert_history_equal(hist, exp)

        # current trial id is not accessible outside of the trial
        with pytest.raises(TrialIDNotFoundError):
            ex.current_trial_id

        ex._delete_cache()

    def test_autoload(self):
        ex = daskperiment.Experiment(id="test_autoload", backend=self.backend)
        a = ex.parameter("a")
        trial_id = ex.trial_id

        @ex.result
        def inc(a):
            return a + 1

        res = inc(a)

        ex.set_parameters(a=1)
        assert res.compute() == 2

        ex.set_parameters(a=3)
        assert res.compute() == 4

        assert ex.trial_id == trial_id + 2
        ex2 = daskperiment.Experiment(id="test_autoload", backend=self.backend)
        assert ex is ex2
        assert ex2.trial_id == trial_id + 2

        # DO NOT DELETE CACHE to test auto-loaded instance
        # ex._delete_cache()

    @pytest.mark.parametrize('random_func', [random.random,
                                             np.random.random])
    def test_random(self, random_func):
        ex = daskperiment.Experiment(id="test_random",
                                     backend=self.backend)

        @ex.result
        def rand():
            return random_func()

        res = rand()
        # result should be different (in almost all cases)
        assert res.compute() != res.compute()

        ex._delete_cache()

    @pytest.mark.parametrize('random_func', [random.random,
                                             np.random.random])
    def test_random_seed(self, random_func):
        ex = daskperiment.Experiment(id="test_random",
                                     backend=self.backend)

        @ex.result
        def rand():
            return random_func()

        res = rand()
        assert res.compute(seed=1) != res.compute(seed=2)
        assert res.compute(seed=1) == res.compute(seed=1)

        ex._delete_cache()

    @pytest.mark.parametrize('random_func', [random.random,
                                             np.random.random])
    def test_random_seed_global(self, random_func):
        ex = daskperiment.Experiment(id="test_random",
                                     backend=self.backend,
                                     seed=1)

        @ex.result
        def rand():
            return random_func()

        res = rand()
        assert res.compute() == res.compute()
        assert res.compute() == res.compute(seed=1)
        assert res.compute(seed=1) != res.compute(seed=2)
        assert res.compute(seed=1) == res.compute(seed=1)

        ex._delete_cache()

    def test_metric(self):
        ex = daskperiment.Experiment(id="test_metric", backend=self.backend)
        a = ex.parameter('a')
        assert ex.trial_id == 0

        @ex.result
        def inc(a):
            ex.save_metric('dummy_metric', epoch=1, value=2)
            ex.save_metric('dummy_metric', epoch=2, value=4)
            return a + 1

        res = inc(a)
        ex.set_parameters(a=3)
        assert res.compute() == 4
        assert ex.trial_id == 1

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
        assert ex.trial_id == 2

        res = ex.load_metric('dummy_metric2', trial_id=[2])
        exp_idx = pd.Index([1], name='Epoch')
        exp_columns = pd.Index([2], name='Trial ID')
        exp = pd.DataFrame({2: [5]}, index=exp_idx, columns=exp_columns)
        tm.assert_frame_equal(res, exp)

        res = inc(a)
        ex.set_parameters(a=4)
        assert res.compute() == 5
        assert ex.trial_id == 3

        res = ex.load_metric('dummy_metric', trial_id=[1, 3])
        exp_idx = pd.Index([1, 2], name='Epoch')
        exp_columns = pd.Index([1, 3], name='Trial ID')
        exp = pd.DataFrame({1: [2, 4], 3: [2, 4]},
                           index=exp_idx, columns=exp_columns)
        tm.assert_frame_equal(res, exp)

        ex._delete_cache()

    def test_metric_invalid_trial_id(self):
        ex = daskperiment.Experiment(id="test_metric_invalid",
                                     backend=self.backend)
        a = ex.parameter('a')
        assert ex.trial_id == 0

        @ex.result
        def inc(a):
            ex.save_metric('dummy_metric', epoch=1, value=2)
            ex.save_metric('dummy_metric', epoch=2, value=4)
            return a + 1

        res = inc(a)
        ex.set_parameters(a=3)
        assert res.compute() == 4
        assert ex.trial_id == 1

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

        with pytest.raises(ValueError,
                           match=('Unable to find saved metric '
                                  'with specified key:')):
            ex.load_metric('invalid_metric', trial_id=1)

        @ex.result
        def inc(a):
            return a + 1

        res = inc(a)
        ex.set_parameters(a=4)
        assert res.compute() == 5
        assert ex.trial_id == 2

        with pytest.raises(TrialIDNotFoundError, match=match):
            ex.load_metric('dummy_metric', trial_id=2)

        ex._delete_cache()

    def test_code(self):
        ex = daskperiment.Experiment(id="test_code", backend=self.backend)
        a = ex.parameter("a")

        @ex
        def inc(a):
            return a + 1

        @ex.result
        def add(a, b):
            return a + b

        res = add(inc(a), a)

        exp = """@ex
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

        if isinstance(ex._backend, LocalBackend):
            assert (ex._backend.code_dir / "test_code_1.py").is_file()

        match = 'Unable to find trial id:'
        with pytest.raises(TrialIDNotFoundError, match=match):
            ex.get_code(trial_id=0)
        with pytest.raises(TrialIDNotFoundError, match=match):
            ex.get_code(trial_id=2)

        ex._delete_cache()

    def test_code_persist(self):
        ex = daskperiment.Experiment(id="test_code_persist",
                                     backend=self.backend)
        a = ex.parameter("a")

        @ex.persist
        def inc(a):
            return a + 1

        @ex.result
        def add(a, b):
            return a + b

        res = add(inc(a), a)

        exp = """@ex.persist
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

    def test_environment(self):
        ex = daskperiment.Experiment(id="test_environment",
                                     backend=self.backend)
        trial_id = ex.trial_id
        a = ex.parameter("a")

        @ex.result
        def inc2(a):
            return a + 2

        res = inc2(a)

        ex.set_parameters(a=3)
        assert res.compute() == 5

        def assert_env(env):
            assert isinstance(env, str)

            lines = env.splitlines()
            assert len(lines) == 11

            assert lines[0].startswith('Platform Information:')
            assert lines[1].startswith('Device CPU Count:')
            assert lines[2].startswith('Python Implementation:')
            assert lines[3].startswith('Python Version:')
            assert lines[4].startswith('Python Shell Mode:')
            assert lines[5].startswith('Daskperiment Version:')
            assert lines[6].startswith('Daskperiment Path:')
            assert lines[7].startswith('Working Directory:')
            assert lines[8].startswith('Git Repository:')
            assert lines[9].startswith('Git Active Branch:')
            assert lines[10].startswith('Git HEAD Commit:')

        env = ex.get_environment()
        assert_env(env)
        assert env.splitlines()[2] == 'Python Implementation: CPython'

        env2 = ex.get_environment(trial_id + 1)
        assert_env(env2)
        assert env == env2

        pkg = ex.get_python_packages()
        assert any(r.startswith('pandas==') for r in pkg.splitlines()), pkg

        pkg2 = ex.get_python_packages(trial_id + 1)
        assert pkg == pkg2
