import daskperiment
from daskperiment.backend import MongoBackend
from daskperiment.testing import CleanupMixin, ex  # noqa
from .base import ExperimentBase


class TestMongoExperiment(ExperimentBase, CleanupMixin):

    backend = 'mongodb://localhost:27017/test_db'

    def test_mongo_init_db(self):
        import pymongo
        uri = 'mongodb://localhost:27017'
        client = pymongo.MongoClient(uri)
        exp = daskperiment.Experiment('test_mongo_init_db',
                                      backend=client.test_db)
        assert isinstance(exp._backend, MongoBackend)

        assert exp._backend.uri == 'mongodb://localhost:27017/test_db'
        assert exp._backend.client is client
