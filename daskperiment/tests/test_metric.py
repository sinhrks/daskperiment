import pytest

import numpy as np
import pandas as pd
import pandas.testing as tm

from daskperiment.core.errors import TrialIDNotFoundError
from daskperiment.core.metric import MetricManager, Metric


class TestMetric(object):

    def test_save(self):
        m = Metric('dummy_metric')

        m.save(trial_id=11, epoch=1, value=2)

        res = m.load(trial_id=11)
        exp_idx = pd.Index([1], name='Epoch')
        exp_columns = pd.Index([11], name='Trial ID')
        exp = pd.DataFrame({11: [2]}, index=exp_idx, columns=exp_columns)
        tm.assert_frame_equal(res, exp)

        m.save(trial_id=11, epoch=2, value=3)
        m.save(trial_id=11, epoch=3, value=4)

        res = m.load(trial_id=11)
        exp_idx = pd.Index([1, 2, 3], name='Epoch')
        exp_columns = pd.Index([11], name='Trial ID')
        exp = pd.DataFrame({11: [2, 3, 4]}, index=exp_idx, columns=exp_columns)
        tm.assert_frame_equal(res, exp)

    def test_save_multi_trial_id(self):
        m = Metric('dummy_metric')
        m.save(trial_id=11, epoch=1, value=2)
        m.save(trial_id=11, epoch=2, value=3)
        m.save(trial_id=11, epoch=3, value=4)

        m.save(trial_id=12, epoch=1, value=5)

        res = m.load(trial_id=12)
        exp_idx = pd.Index([1], name='Epoch')
        exp_columns = pd.Index([12], name='Trial ID')
        exp = pd.DataFrame({12: [5]}, index=exp_idx, columns=exp_columns)
        tm.assert_frame_equal(res, exp)

        res = m.load(trial_id=[11, 12])
        exp_idx = pd.Index([1, 2, 3], name='Epoch')
        exp_columns = pd.Index([11, 12], name='Trial ID')
        exp = pd.DataFrame({11: [2, 3, 4],
                            12: [5, np.nan, np.nan]},
                           index=exp_idx, columns=exp_columns)
        tm.assert_frame_equal(res, exp)

        m.save(trial_id=15, epoch=1, value=10)
        m.save(trial_id=15, epoch=2, value=11)

        res = m.load(trial_id=[12, 15])
        exp_idx = pd.Index([1, 2], name='Epoch')
        exp_columns = pd.Index([12, 15], name='Trial ID')
        exp = pd.DataFrame({12: [5, np.nan],
                            15: [10, 11]},
                           index=exp_idx, columns=exp_columns)
        tm.assert_frame_equal(res, exp)


class TestMetricManager(object):

    def test_save(self):
        m = MetricManager()

        m.save('dummy_metric', trial_id=11, epoch=1, value=2)
        res = m.load('dummy_metric', trial_id=[11])
        exp_idx = pd.Index([1], name='Epoch')
        exp_columns = pd.Index([11], name='Trial ID')
        exp = pd.DataFrame({11: [2]}, index=exp_idx, columns=exp_columns)
        tm.assert_frame_equal(res, exp)

        m.save('dummy_metric2', trial_id=11, epoch=1, value=5)
        res = m.load('dummy_metric2', trial_id=[11])
        exp_idx = pd.Index([1], name='Epoch')
        exp_columns = pd.Index([11], name='Trial ID')
        exp = pd.DataFrame({11: [5]}, index=exp_idx, columns=exp_columns)
        tm.assert_frame_equal(res, exp)

        res = m.load('dummy_metric', trial_id=[11])
        exp_idx = pd.Index([1], name='Epoch')
        exp_columns = pd.Index([11], name='Trial ID')
        exp = pd.DataFrame({11: [2]}, index=exp_idx, columns=exp_columns)
        tm.assert_frame_equal(res, exp)

    def test_error(self):
        m = MetricManager()

        m.save('dummy_metric', trial_id=11, epoch=1, value=2)
        with pytest.raises(ValueError):
            m.load('wrong_metric', trial_id=[11])

        with pytest.raises(TrialIDNotFoundError):
            m.load('dummy_metric', trial_id=[99])

        with pytest.raises(TrialIDNotFoundError):
            m.load('dummy_metric', trial_id=[11, 99])
