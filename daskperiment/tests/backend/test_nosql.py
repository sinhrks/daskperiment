import pytest

import pickle

import pandas as pd

from daskperiment.backend import MongoBackend, RedisBackend
from daskperiment.backend.mongo import MongoKey


class NoSQLBase(object):

    @classmethod
    def init_backend(cls):
        raise NotImplementedError

    def make_key(self, key):
        """
        Create key to backend
        """
        return key

    def make_expected(self, exp):
        """
        Convert expected input to DB internal repr
        """
        return exp

    @classmethod
    def teardown_class(cls):
        backend = cls.init_backend()
        backend._delete_cache()

    def test_set_get(self):
        backend = self.init_backend()

        key = self.make_key('test_key')
        backend.set(key, 0)
        assert backend.get(key) == self.make_expected(0)

    def test_get_not_exist(self):
        backend = self.init_backend()
        key = self.make_key('no_key')
        assert backend.get(key) is None

    @pytest.mark.parametrize('key_string', ['list_key', 'dot_list_key.child',
                                            'num_list_key.series.1'])
    def test_append_list(self, key_string):
        backend = self.init_backend()

        key = self.make_key(key_string)
        backend.append_list(key, 10)
        assert backend.get_list(key) == self.make_expected([10])

        backend.append_list(key, 20)
        assert backend.get_list(key) == self.make_expected([10, 20])

        backend.append_list(key, 30)
        backend.append_list(key, 40)
        assert backend.get_list(key) == self.make_expected([10, 20, 30, 40])

        new_key = self.make_key(key_string + '2')
        backend.append_list(new_key, 1)
        assert backend.get_list(new_key) == self.make_expected([1])
        assert backend.get_list(key) == self.make_expected([10, 20, 30, 40])

    def test_no_list_key(self):
        backend = self.init_backend()
        key = self.make_key('no_list')
        assert backend.get_list(key) == []
        assert backend.get(key) is None

    def test_increment(self):
        backend = self.init_backend()

        key = self.make_key('incr_key')
        assert backend.increment(key) == 1
        assert backend.increment(key) == 2
        assert backend.increment(key) == 3
        assert backend.increment(key) == 4

        new_key = self.make_key('new_incr_key')
        assert backend.increment(new_key) == 1
        assert backend.increment(key) == 5

    def test_save_load_text(self):
        backend = self.init_backend()

        key = self.make_key('text_key')
        backend.save_text(key, 'aaa')
        assert backend.load_text(key) == 'aaa'

        backend.save_text(key, 'bbb')
        assert backend.load_text(key) == 'bbb'

    @pytest.mark.parametrize('key_string', ['obj_key', 'num_obj_key.series.1'])
    def test_save_load_object(self, key_string):
        backend = self.init_backend()
        obj = {'a': 1, 'b': pd.Timestamp('2011-01-01')}

        key = self.make_key(key_string)
        backend.save_object(key, obj)
        assert backend.load_object(key) == obj

    def test_pickle_roundtrip_save_load_object(self):
        backend = self.init_backend()

        pickle_obj_key = self.make_key('pickle_obj_key')
        obj = {'a': 1, 'b': pd.Timestamp('2011-01-01')}
        backend.save_object(pickle_obj_key, obj)
        assert backend.load_object(pickle_obj_key) == obj

        pickle_text_key = self.make_key('pickle_text_key')
        backend.save_object(pickle_text_key, 'xxxx')
        assert backend.load_object(pickle_text_key) == 'xxxx'

        new_backend = pickle.loads(pickle.dumps(backend))
        assert new_backend.load_object(pickle_obj_key) == obj
        assert new_backend.load_object(pickle_text_key) == 'xxxx'

        assert backend.load_object(pickle_obj_key) == obj
        assert backend.load_object(pickle_text_key) == 'xxxx'


class TestRedisBackend(NoSQLBase):

    @classmethod
    def init_backend(cls):
        uri = 'redis://localhost:6379/0'
        return RedisBackend('redis_backend', uri)

    def make_expected(self, exp):
        if isinstance(exp, int):
            return str(exp).encode()
        elif isinstance(exp, list):
            return [self.make_expected(e) for e in exp]
        else:
            raise NotImplementedError


class TestMongoBackend(NoSQLBase):

    @classmethod
    def init_backend(cls):
        uri = 'mongodb://localhost:27017/test_db'
        return MongoBackend('mongo_backend', uri)

    def make_key(self, key):
        return MongoKey({'test_mongo_key': key})

    def test_mongo_key(self):
        backend = self.init_backend()

        key = MongoKey({'experiment_id': 'test_mongo_key',
                        'trial_id': 1})

        backend.set(key, 100)
        assert backend.get(key) == 100
        backend.set(key, 200)
        assert backend.get(key) == 200

        new_key = MongoKey({'experiment_id': 'test_mongo_key',
                            'trial_id': 2})

        backend.set(new_key, 300)
        assert backend.get(new_key) == 300
        assert backend.get(key) == 200

    def test_mongo_key_internal(self):
        backend = self.init_backend()

        key = MongoKey({'experiment_id': 'test_mongo_key_internal',
                        'trial_id': 1354,
                        'internal_unique_key': 'xxxxx'})

        backend.set(key, 100)
        assert backend.get(key) == 100

        key = MongoKey({'internal_unique_key': 'xxxxx'},
                       field_name='experiment_id')
        assert backend.get(key) == 'test_mongo_key_internal'

        key = MongoKey({'internal_unique_key': 'xxxxx'},
                       field_name='trial_id')
        assert backend.get(key) == 1354

    def test_append_list_mongo_key(self):
        backend = self.init_backend()

        key = MongoKey({'experiment_id': 'test_append_list_mongo_key',
                        'trial_id': 1})

        backend.append_list(key, 10)
        assert backend.get_list(key) == [10]

        backend.append_list(key, 20)
        assert backend.get_list(key) == [10, 20]

    def test_increment_mongo_key(self):
        backend = self.init_backend()

        key = MongoKey({'experiment_id': 'test_increment_mongo_key',
                        'trial_id': 1})

        assert backend.increment(key) == 1
        assert backend.increment(key) == 2
        assert backend.increment(key) == 3
        assert backend.increment(key) == 4

        new_key = MongoKey({'experiment_id': 'test_increment_mongo_key',
                            'trial_id': 2})
        assert backend.increment(new_key) == 1
        assert backend.increment(key) == 5


class TestMongoKey(object):

    def test_eq(self):
        key1 = MongoKey({'doc': 1, 'id': 2})
        key2 = MongoKey({'doc': 1, 'id': 2})
        assert key1 == key2

        key3 = MongoKey({'doc': 1, 'id': 3})
        assert key1 != key3

        key4 = MongoKey({'doc': 1, 'id': 2}, field_name='xxx')
        assert key1 != key4
        assert key2 != key4

    def test_repr(self):
        key = MongoKey({'doc': 1, 'id': 2})
        exp = "MongoKey(meta={'doc': 1, 'id': 2}, field_name=value)"
        assert repr(key) == exp

    def test_wildcard(self):
        key = MongoKey({'key1': 1, 'key2': 2, 'key3': '*'})
        assert key.document_meta == {'key1': 1, 'key2': 2}
