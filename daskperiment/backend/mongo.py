import os

from daskperiment.backend.base import _NoSQLBackend
from daskperiment.util.log import get_logger


logger = get_logger(__name__)


class MongoBackend(_NoSQLBackend):

    _SEP = '.'

    def __init__(self, experiment_id, uri):
        super().__init__(experiment_id)
        # print(uri)
        # uri = str(uri)
        # TODO: handle mongo DB instance
        self.uri = uri

    @property
    def client(self):
        if not hasattr(self, '_client'):
            import pymongo
            self._client = pymongo.MongoClient(self.uri)
        return self._client

    @property
    def dbname(self):
        return os.path.basename(self.uri)

    @property
    def collection(self):
        """
        Get MongoDB DocumentCollection named with experiment ID
        """
        if not hasattr(self, '_collection'):
            db = self.client[self.dbname]
            self._collection = db[self.experiment_id]
        return self._collection

    def set(self, key, value):
        return self.collection.insert_one({'_id': key, 'value': value})

    def get(self, key):
        doc = self.collection.find_one({'_id': key})
        if doc is None:
            return None
        return doc['value']

    def keys(self, key):
        # TODO: support wildcard
        keys = self.collection.find({'_id': key})
        # TODO: handling child
        return [key for k in keys]

    def append_list(self, key, value):
        self.collection.update_one({'_id': key},
                                   {'$push': {'list': value}})

    def get_list(self, key):
        return self.get(key)

    def increment(self, key):
        from pymongo import ReturnDocument
        c = self.collection
        result = c.find_one_and_update({'_id': key},
                                       {'$inc': {'value': 1}},
                                       upsert=True,
                                       return_document=ReturnDocument.AFTER)

        return result['value']

    def _delete_cache(self):
        self.client.drop_database(self.dbname)
