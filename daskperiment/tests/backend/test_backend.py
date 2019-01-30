import pickle

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

    def test_redis_pickle(self):
        backend = 'redis://localhost:6379/0'
        r = RedisBackend(backend)
        res = pickle.loads(pickle.dumps(r))
        assert res.uri == backend
