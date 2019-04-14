from daskperiment.backend import MongoBackend, RedisBackend


class NoSQLBase(object):

    @classmethod
    def init_backend(cls):
        raise NotImplementedError

    @classmethod
    def teardown_class(cls):
        backend = cls.init_backend()
        backend._delete_cache()

    def test_set_get(self):
        backend = self.init_backend()

        backend.set('test_key', 0)
        backend.get('test_key') == 0

    def test_get_not_exist(self):
        backend = self.init_backend()

        backend.get('no_key') is None

    def test_keys(self):
        backend = self.init_backend()

        backend.set('new_key', 100)
        backend.get('new_key') == 0

        keys = backend.keys('new_key')
        assert 'new_key' in keys

    def test_append_list(self):
        backend = self.init_backend()

        backend.append_list('list_key', 10)
        backend.get_list('list_key') == [10]

        backend.append_list('list_key', 20)
        backend.get_list('list_key') == [10, 20]

        backend.append_list('list_key', 30)
        backend.append_list('list_key', 40)
        backend.get_list('list_key') == [10, 20, 30, 40]

        backend.append_list('new_list_key', 1)
        backend.get_list('newlist_key') == [1]
        backend.get_list('list_key') == [10, 20, 30, 40]

    def test_increment(self):
        backend = self.init_backend()
        assert backend.increment('incr_key') == 1
        assert backend.increment('incr_key') == 2
        assert backend.increment('incr_key') == 3
        assert backend.increment('incr_key') == 4

        assert backend.increment('new_incr') == 1
        assert backend.increment('incr_key') == 5


class TestRedisBackend(NoSQLBase):

    @classmethod
    def init_backend(cls):
        uri = 'redis://localhost:6379/0'
        return RedisBackend('redis_backend', uri)


class TestMongoBackend(NoSQLBase):

    @classmethod
    def init_backend(cls):
        uri = 'mongodb://localhost:27017/test_db'
        return MongoBackend('mongo_backend', uri)
