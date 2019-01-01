import daskperiment.io.pickle as pickle
from .base import IOBase


class TestPickle(IOBase):

    def dumps(self, obj):
        return pickle.dumps(obj)

    def loads(self, obj):
        return pickle.loads(obj)
