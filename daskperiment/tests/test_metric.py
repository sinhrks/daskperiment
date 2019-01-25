import numpy as np
import pandas as pd
import pandas.testing as tm

from daskperiment.core.metric import MetricManager, Metric


class TestMetric(object):

    def test_save(self):
        m = Metric('dummy_metric')

        m.save(trial_id=11, epoch=1, value=2)

        res = m.load(trial_id=11)
        exp_idx = pd.Index([1], name='Epoch')
        exp = pd.DataFrame({11: [2]}, exp_idx)
        tm.assert_frame_equal(res, exp)

        m.save(trial_id=11, epoch=2, value=3)
        m.save(trial_id=11, epoch=3, value=4)

        res = m.load(trial_id=11)
        exp_idx = pd.Index([1, 2, 3], name='Epoch')
        exp = pd.DataFrame({11: [2, 3, 4]}, exp_idx)
        tm.assert_frame_equal(res, exp)

    def test_save_multi_trial_id(self):
        m = Metric('dummy_metric')
        m.save(trial_id=11, epoch=1, value=2)
        m.save(trial_id=11, epoch=2, value=3)
        m.save(trial_id=11, epoch=3, value=4)

        m.save(trial_id=12, epoch=1, value=5)

        res = m.load(trial_id=12)
        exp_idx = pd.Index([1], name='Epoch')
        exp = pd.DataFrame({12: [5]}, exp_idx)
        tm.assert_frame_equal(res, exp)

        res = m.load(trial_id=[11, 12])
        exp_idx = pd.Index([1, 2, 3], name='Epoch')
        exp = pd.DataFrame({11: [2, 3, 4],
                            12: [5, np.nan, np.nan]}, exp_idx)
        tm.assert_frame_equal(res, exp)

        m.save(trial_id=15, epoch=1, value=10)
        m.save(trial_id=15, epoch=2, value=11)

        res = m.load(trial_id=[12, 15])
        exp_idx = pd.Index([1, 2], name='Epoch')
        exp = pd.DataFrame({12: [5, np.nan],
                            15: [10, 11]}, exp_idx)
        tm.assert_frame_equal(res, exp)


class TestMetricManager(object):

    def test_save(self):
        m = MetricManager()

        m.save('dummy_metric', trial_id=11, epoch=1, value=2)
        res = m.load('dummy_metric', trial_id=[11])
        exp_idx = pd.Index([1], name='Epoch')
        exp = pd.DataFrame({11: [2]}, exp_idx)
        tm.assert_frame_equal(res, exp)

        m.save('dummy_metric2', trial_id=11, epoch=1, value=5)
        res = m.load('dummy_metric2', trial_id=[11])
        exp_idx = pd.Index([1], name='Epoch')
        exp = pd.DataFrame({11: [5]}, exp_idx)
        tm.assert_frame_equal(res, exp)

        res = m.load('dummy_metric', trial_id=[11])
        exp_idx = pd.Index([1], name='Epoch')
        exp = pd.DataFrame({11: [2]}, exp_idx)
        tm.assert_frame_equal(res, exp)
