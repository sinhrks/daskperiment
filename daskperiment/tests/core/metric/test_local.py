import pytest

import pandas as pd
import pandas.testing as tm

from daskperiment.core.errors import TrialIDNotFoundError
from daskperiment.core.metric.local import Metric
from .base import MetricManagerBase


class TestLocalMetricManager(MetricManagerBase):

    @property
    def backend(self):
        from daskperiment.config import _CACHE_DIR
        cache = _CACHE_DIR / 'local_metric_manager_test'
        return cache


class TestMetric(object):

    def test_save(self):
        m = Metric('dummy_metric')

        m.save(trial_id=11, epoch=1, value=2)

        res = m._load_single(trial_id=11)
        exp_idx = pd.Index([1], name='Epoch')
        exp = pd.Series([2], index=exp_idx, name=11)
        tm.assert_series_equal(res, exp)

        m.save(trial_id=11, epoch=2, value=3)
        m.save(trial_id=11, epoch=3, value=4)

        res = m._load_single(trial_id=11)
        exp_idx = pd.Index([1, 2, 3], name='Epoch')
        exp = pd.Series([2, 3, 4], index=exp_idx, name=11)
        tm.assert_series_equal(res, exp)

        match = 'Unable to find trial id:'
        with pytest.raises(TrialIDNotFoundError, match=match):
            m._load_single(trial_id=12)
