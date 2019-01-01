import datetime

import pandas as pd


class IOBase(object):

    def dumps(self, obj):
        raise NotImplementedError

    def loads(self, obj):
        raise NotImplementedError

    def test_roundtrip_primitive(self):
        params = dict(a=1, b=1.1, c=True, d='xx')

        res = self.loads(self.dumps(params))
        assert res == params

    def test_roundtrip_datetimelike(self):
        params = dict(a=pd.Timestamp('2011-01-01'),
                      b=pd.Timedelta(1),
                      c=datetime.datetime(2012, 2, 2),
                      d=datetime.timedelta(2))

        res = self.loads(self.dumps(params))
        assert res == params
