import pickle

import pandas as pd

import daskperiment
from daskperiment.backend import LocalBackend, RedisBackend


class TestBackend(object):

    def test_local_backend(self):
        ex = daskperiment.Experiment('local_backend', backend='local')
        assert isinstance(ex._backend, LocalBackend)

        ex._delete_cache()

    def test_redis_backend(self):
        backend = 'redis://localhost:6379/0'
        ex = daskperiment.Experiment('redis_backend', backend=backend)
        assert isinstance(ex._backend, RedisBackend)
        assert ex._backend.uri == backend

    def test_redis_backend_picklable(self):
        backend = 'redis://localhost:6379/0'
        r = RedisBackend('redis_experiment', backend)
        res = pickle.loads(pickle.dumps(r))
        assert res.uri == backend

    def test_redis_pickle_roundtrip(self):
        backend = 'redis://localhost:6379/0'
        r = RedisBackend('redis_experiment', backend)

        obj = dict(a=1, b=2)
        r.save_object('redis_experiment:obj', obj)
        res = r.load_object('redis_experiment:obj')
        assert res == obj

        obj = dict(a=pd.Timestamp('2011-01-01'), b=[1, 2, 4])
        r.save_object('redis_experiment:obj', obj)
        res = r.load_object('redis_experiment:obj')
        assert res == obj
