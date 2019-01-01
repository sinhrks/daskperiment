import pytest

import datetime

import pandas as pd

import daskperiment.io.json as json
from .base import IOBase


class TestJson(IOBase):

    def dumps(self, obj):
        return json.dumps(obj)

    def loads(self, obj):
        return json.loads(obj)

    @pytest.mark.skipif(pd.__version__ < '0.24.0',
                        reason='ISO Timedelta is not supported')
    def test_roundtrip_datetimelike(self):
        # override to check class change
        params = dict(a=pd.Timestamp('2011-01-01'),
                      b=pd.Timedelta(1),
                      c=datetime.datetime(2012, 2, 2),
                      d=datetime.timedelta(2))

        res = self.loads(self.dumps(params))
        assert res == params
        # datetime obj is converted to pandas types
        assert isinstance(res['c'], pd.Timestamp)
        assert isinstance(res['d'], pd.Timedelta)
