import pandas as pd
import pandas.testing as tm

import daskperiment


class TestExperiment(object):

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

    def test_pattern(self):
        ex = daskperiment.Experiment(id="test_history")
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

        assert ex.get_persisted('inc', trial_id=1) == 2
        assert ex.get_persisted('inc', trial_id=2) == 4

    def test_persist(self):
        ex = daskperiment.Experiment(id="test_history")
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

    def test_metric(self):
        ex = daskperiment.Experiment(id="test_metric")
        assert ex._trial_id == 0

        ex.save_metric('dummy_metric', epoch=1, value=2)
        res = ex.load_metric('dummy_metric', trial_id=[0])
        exp_idx = pd.Index([1], name='Epoch')
        exp = pd.DataFrame({0: [2]}, exp_idx)
        tm.assert_frame_equal(res, exp)

        @ex.result
        def dummy():
            return 0

        res = dummy()
        res.compute()
        assert ex._trial_id == 1

        ex.save_metric('dummy_metric2', epoch=1, value=5)
        res = ex.load_metric('dummy_metric2', trial_id=[1])
        exp_idx = pd.Index([1], name='Epoch')
        exp = pd.DataFrame({1: [5]}, exp_idx)
        tm.assert_frame_equal(res, exp)

        ex.save_metric('dummy_metric', epoch=1, value=6)
        res = ex.load_metric('dummy_metric', trial_id=[0, 1])
        exp_idx = pd.Index([1], name='Epoch')
        exp = pd.DataFrame({0: [2], 1: [6]}, exp_idx)
        tm.assert_frame_equal(res, exp)
