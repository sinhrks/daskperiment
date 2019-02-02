import pytest

import pickle

import pandas as pd
import redis

import daskperiment
from daskperiment.backend import (init_backend, LocalBackend,
                                  RedisBackend)


class TestInitBackend(object):

    def test_local_init_str(self):
        b = init_backend('local_backend', backend='local')
        assert isinstance(b, LocalBackend)

        exp = daskperiment.config._CACHE_DIR / 'local_backend'
        assert b.cache_dir == exp

    def test_local_init_path(self):
        p = daskperiment.config._CACHE_DIR / 'local_backend'
        b = init_backend('local_backend', backend=p)
        assert isinstance(b, LocalBackend)

        assert b.cache_dir == p

    @pytest.mark.parametrize('backend', ['redis://localhost:6379/0',
                                         'redis://dumy:9999/1'
                                         'rediss://localhost:6379/0'])
    def test_redis_init_protocol(self, backend):
        b = init_backend('local_backend', backend=backend)
        assert isinstance(b, RedisBackend)

        assert b.uri == backend

    def test_redis_init_pool(self):
        uri = 'redis://localhost:6379/0'
        backend = redis.ConnectionPool.from_url(uri)
        b = init_backend('local_backend', backend=backend)
        assert isinstance(b, RedisBackend)

        assert b.uri == uri

    def test_maybe_redis(self):
        from daskperiment.backend.base import maybe_redis
        assert maybe_redis('redis://xxx')
        assert not maybe_redis('xxx://xxx')
        assert not maybe_redis('http://xxx')
        assert not maybe_redis(3)
        assert not maybe_redis('local')

        uri = 'redis://localhost:6379/0'
        pool = redis.ConnectionPool.from_url(uri)
        assert maybe_redis(pool)


class TestBackend(object):

    def test_local_backend(self):
        ex = daskperiment.Experiment('local_backend', backend='local')
        assert isinstance(ex._backend, LocalBackend)

        exp = "LocalBackend('daskperiment_cache/local_backend')"
        assert repr(ex._backend) == exp

        ex._delete_cache()

    def test_redis_backend(self):
        backend = 'redis://localhost:6379/0'
        ex = daskperiment.Experiment('redis_backend', backend=backend)
        assert isinstance(ex._backend, RedisBackend)
        assert ex._backend.uri == backend

        exp = "RedisBackend('redis://localhost:6379/0')"
        assert repr(ex._backend) == exp

    def test_locak_backend_eq(self):
        r = init_backend('local_backend', backend='local')
        assert r == r
        r2 = init_backend('local_backend', backend='local')
        assert r2 == r
        assert r == r2

        r2 = init_backend('local_backend2', backend='local')
        assert r2 != r
        assert r != r2

    def test_local_backend_picklable(self):
        r = init_backend('local_backend', backend='local')
        res = pickle.loads(pickle.dumps(r))
        assert r == res
        assert res.cache_dir == r.cache_dir

    def test_redis_backend_picklable(self):
        backend = 'redis://localhost:6379/0'
        r = RedisBackend('redis_experiment', backend)
        res = pickle.loads(pickle.dumps(r))
        assert r == res
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
