from dask.base import tokenize


def get_hash(*args, **kwargs):
    return tokenize(*args, **kwargs)
