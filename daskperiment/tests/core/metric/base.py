import pytest

import numpy as np
import pandas as pd
import pandas.testing as tm

import daskperiment
from daskperiment.backend import init_backend
from daskperiment.core.errors import TrialIDNotFoundError


class MetricManagerBase(object):

    @property
    def backend(self):
        raise NotImplementedError

    @property
    def metrics(self):
        return init_backend('dummy_experiment', self.backend).metrics

    def test_invalid_id(self):
        m = self.metrics

        msg = 'Metric name must be str, given:'
        with pytest.raises(ValueError, match=msg):
            m.save(1, trial_id=11, epoch=1, value=2)

        msg = 'Metric name cannot contain colon '
        with pytest.raises(ValueError, match=msg):
            m.save("aa:aa", trial_id=11, epoch=1, value=2)

    def test_save(self):
        m = self.metrics

        m.save('dummy_metric1', trial_id=11, epoch=1, value=2)
        res = m.load('dummy_metric1', trial_id=[11])
        exp_idx = pd.Index([1], name='Epoch')
        exp_columns = pd.Index([11], name='Trial ID')
        exp = pd.DataFrame({11: [2]}, index=exp_idx, columns=exp_columns)
        tm.assert_frame_equal(res, exp)

        assert m.keys() == ['dummy_metric1']

        m.save('dummy_metric2', trial_id=11, epoch=1, value=5)
        res = m.load('dummy_metric2', trial_id=[11])
        exp_idx = pd.Index([1], name='Epoch')
        exp_columns = pd.Index([11], name='Trial ID')
        exp = pd.DataFrame({11: [5]}, index=exp_idx, columns=exp_columns)
        tm.assert_frame_equal(res, exp)

        res = m.load('dummy_metric1', trial_id=[11])
        exp_idx = pd.Index([1], name='Epoch')
        exp_columns = pd.Index([11], name='Trial ID')
        exp = pd.DataFrame({11: [2]}, index=exp_idx, columns=exp_columns)
        tm.assert_frame_equal(res, exp)

    def test_save_multi_trial_id(self):
        m = self.metrics

        m.save('dummy_metric3', trial_id=11, epoch=1, value=2)
        m.save('dummy_metric3', trial_id=11, epoch=2, value=3)
        m.save('dummy_metric3', trial_id=11, epoch=3, value=4)

        m.save('dummy_metric3', trial_id=12, epoch=1, value=5)

        res = m.load('dummy_metric3', trial_id=12)
        exp_idx = pd.Index([1], name='Epoch')
        exp_columns = pd.Index([12], name='Trial ID')
        exp = pd.DataFrame({12: [5]}, index=exp_idx, columns=exp_columns)
        tm.assert_frame_equal(res, exp)

        res = m.load('dummy_metric3', trial_id=[11, 12])
        exp_idx = pd.Index([1, 2, 3], name='Epoch')
        exp_columns = pd.Index([11, 12], name='Trial ID')
        exp = pd.DataFrame({11: [2, 3, 4],
                            12: [5, np.nan, np.nan]},
                           index=exp_idx, columns=exp_columns)
        tm.assert_frame_equal(res, exp)

        m.save('dummy_metric3', trial_id=15, epoch=1, value=10)
        m.save('dummy_metric3', trial_id=15, epoch=2, value=11)

        res = m.load('dummy_metric3', trial_id=[12, 15])
        exp_idx = pd.Index([1, 2], name='Epoch')
        exp_columns = pd.Index([12, 15], name='Trial ID')
        exp = pd.DataFrame({12: [5, np.nan],
                            15: [10, 11]},
                           index=exp_idx, columns=exp_columns)
        tm.assert_frame_equal(res, exp)

    def test_error(self):
        m = self.metrics

        m.save('error_metric', trial_id=11, epoch=1, value=2)
        with pytest.raises(ValueError):
            m.load('wrong_metric', trial_id=[11])

        match = 'Unable to find trial id:'
        with pytest.raises(TrialIDNotFoundError, match=match):
            m.load('error_metric', trial_id=[99])

        with pytest.raises(TrialIDNotFoundError, match=match):
            m.load('error_metric', trial_id=[11, 99])

    def test_metric_experiment(self):
        ex = daskperiment.Experiment('metric_experiment', backend=self.backend)
        a = ex.parameter('a')

        @ex.result
        def dummy(a):
            ex.save_metric('exp_metric1', epoch=1, value=a + 1)
            ex.save_metric('exp_metric1', epoch=3, value=a + 2)
            ex.save_metric('exp_metric2', epoch=1, value=a + 11)
            ex.save_metric('exp_metric2', epoch=3, value=a + 12)
            return a + 1

        res = dummy(a)

        ex.set_parameters(a=1)
        assert res.compute() == 2
        ex.set_parameters(a=2)
        assert res.compute() == 3

        assert ex._metrics.keys() == ['exp_metric1', 'exp_metric2']

        res = ex.load_metric('exp_metric1', trial_id=[1, 2])
        exp_idx = pd.Index([1, 3], name='Epoch')
        exp_columns = pd.Index([1, 2], name='Trial ID')
        exp = pd.DataFrame({1: [2, 3], 2: [3, 4]},
                           index=exp_idx, columns=exp_columns)
        tm.assert_frame_equal(res, exp)

        res = ex.load_metric('exp_metric2', trial_id=[1, 2])
        exp_idx = pd.Index([1, 3], name='Epoch')
        exp_columns = pd.Index([1, 2], name='Trial ID')
        exp = pd.DataFrame({1: [12, 13], 2: [13, 14]},
                           index=exp_idx, columns=exp_columns)
        tm.assert_frame_equal(res, exp)

        # check with another instance
        del daskperiment.Experiment._instance_cache['metric_experiment']
        ex = daskperiment.Experiment('metric_experiment', backend=self.backend)
        assert ex._metrics.keys() == ['exp_metric1', 'exp_metric2']

        res = ex.load_metric('exp_metric1', trial_id=[1, 2])
        exp_idx = pd.Index([1, 3], name='Epoch')
        exp_columns = pd.Index([1, 2], name='Trial ID')
        exp = pd.DataFrame({1: [2, 3], 2: [3, 4]},
                           index=exp_idx, columns=exp_columns)
        tm.assert_frame_equal(res, exp)

        res = ex.load_metric('exp_metric2', trial_id=[1, 2])
        exp_idx = pd.Index([1, 3], name='Epoch')
        exp_columns = pd.Index([1, 2], name='Trial ID')
        exp = pd.DataFrame({1: [12, 13], 2: [13, 14]},
                           index=exp_idx, columns=exp_columns)
        tm.assert_frame_equal(res, exp)

        ex._delete_cache()

    def test_multi_exp(self):
        ex1 = daskperiment.Experiment('multi_exp', backend=self.backend)
        a1 = ex1.parameter('a')

        @ex1.result
        def dummy(a):
            ex1.save_metric('exp_metric3', epoch=1, value=a + 1)
            ex1.save_metric('exp_metric3', epoch=3, value=a + 2)
            return a + 1

        res = dummy(a1)
        ex1.set_parameters(a=1)
        assert res.compute() == 2

        ex2 = daskperiment.Experiment('metric_experiment',
                                      backend=self.backend)
        a2 = ex2.parameter('a')

        @ex2.result
        def dummy(a):
            ex2.save_metric('exp_metric3', epoch=1, value=a + 11)
            ex2.save_metric('exp_metric3', epoch=3, value=a + 12)
            return a + 1

        res = dummy(a2)
        ex2.set_parameters(a=5)
        assert res.compute() == 6

        res = ex1.load_metric('exp_metric3', trial_id=[1])
        exp_idx = pd.Index([1, 3], name='Epoch')
        exp_columns = pd.Index([1], name='Trial ID')
        exp = pd.DataFrame({1: [2, 3]}, index=exp_idx, columns=exp_columns)
        tm.assert_frame_equal(res, exp)

        res = ex2.load_metric('exp_metric3', trial_id=[1])
        exp_idx = pd.Index([1, 3], name='Epoch')
        exp_columns = pd.Index([1], name='Trial ID')
        exp = pd.DataFrame({1: [16, 17]}, index=exp_idx, columns=exp_columns)
        tm.assert_frame_equal(res, exp)

        ex1._delete_cache()
        ex2._delete_cache()
