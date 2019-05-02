import pytest

import numpy as np
import pandas as pd

from daskperiment.util.hashing import get_hash


def assert_hash(h):
    assert isinstance(h, str)
    assert len(h) == 32


class TestHashing(object):

    @pytest.mark.parametrize('obj', [1, 1.1, True, None,
                                     'aaa', 'xxx'])
    def test_hash_scalar(self, obj):
        hashed1 = get_hash(obj)
        hashed2 = get_hash(obj)

        assert_hash(hashed1)
        assert_hash(hashed2)

        assert hashed1 == hashed2

    @pytest.mark.parametrize('obj', [1, 1.1, True, None,
                                     'aaa', 'xxx'])
    def test_hash_scalar_different(self, obj):
        hashed1 = get_hash(obj)
        hashed2 = get_hash('different')

        assert_hash(hashed1)
        assert_hash(hashed2)

        assert hashed1 != hashed2

    def test_hash_object(self):
        hashed1 = get_hash(dict(a=1, b='x'))
        hashed2 = get_hash(dict(a=1, b='x'))

        assert_hash(hashed1)
        assert_hash(hashed2)

        assert hashed1 == hashed2

    def test_hash_object_different(self):
        hashed1 = get_hash(dict(a=1, b='x'))
        hashed2 = get_hash(dict(a=2, b='x'))

        assert_hash(hashed1)
        assert_hash(hashed2)

        assert hashed1 != hashed2

    @pytest.mark.parametrize('dtype', [np.int64, np.float64, object])
    def test_hash_numpy(self, dtype):
        hashed1 = get_hash(np.array([1, 2], dtype=dtype))
        hashed2 = get_hash(np.array([1, 2], dtype=dtype))

        assert_hash(hashed1)
        assert_hash(hashed2)

        assert hashed1 == hashed2

    def test_hash_numpy_different_dtype(self):
        hashed1 = get_hash(np.array([1, 2], dtype=np.int64))
        hashed2 = get_hash(np.array([1, 2], dtype=np.int32))

        assert_hash(hashed1)
        assert_hash(hashed2)

        assert hashed1 != hashed2

    def test_hash_numpy_different_values(self):
        hashed1 = get_hash(np.array([1, 2], dtype=np.int64))
        hashed2 = get_hash(np.array([1, 3], dtype=np.int64))

        assert_hash(hashed1)
        assert_hash(hashed2)

        assert hashed1 != hashed2

    def test_hash_pandas(self):
        df1 = pd.DataFrame(dict(a=[1, 2], b=[3, 4]))
        hashed1 = get_hash(df1)
        df2 = pd.DataFrame(dict(a=[1, 2], b=[3, 4]))
        hashed2 = get_hash(df2)

        assert_hash(hashed1)
        assert_hash(hashed2)

        assert hashed1 == hashed2

    def test_hash_pandas_different(self):
        df1 = pd.DataFrame(dict(a=[1, 2], b=[3, 4]))
        hashed1 = get_hash(df1)
        df2 = pd.DataFrame(dict(a=[1, 2], b=[2, 4]))
        hashed2 = get_hash(df2)

        assert_hash(hashed1)
        assert_hash(hashed2)

        assert hashed1 != hashed2
