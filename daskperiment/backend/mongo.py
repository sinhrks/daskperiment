import os

from daskperiment.backend.base import _NoSQLBackend
from daskperiment.util.log import get_logger


logger = get_logger(__name__)


class MongoKey(object):
    """
    Represents document metadata and field name
    """
    def __init__(self, document_meta, field_name='value'):
        assert isinstance(document_meta, dict)
        # document_meta is a dict stores experiment_id, trial_id etc
        # it must be unique in the collection

        # remove wildcard
        document_meta = {k: v for k, v in document_meta.items() if v != '*'}
        self.document_meta = document_meta
        self.field_name = field_name

    def __repr__(self):
        fmt = 'MongoKey(meta={}, field_name={})'
        return fmt.format(self.document_meta, self.field_name)

    def __eq__(self, other):
        if not isinstance(other, MongoKey):
            return False
        if self.document_meta != other.document_meta:
            return False
        if self.field_name != other.field_name:
            return False
        return True


class MongoBackend(_NoSQLBackend):

    def __init__(self, experiment_id, uri):
        super().__init__(experiment_id)
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

    def get_metric_manager(self):
        from daskperiment.core.metric.nosql import MongoMetricManager
        return MongoMetricManager(backend=self)

    def get_trial_manager(self):
        from daskperiment.core.trial.nosql import MongoTrialManager
        return MongoTrialManager(backend=self)

    ################################################
    # Key & value management
    ################################################

    def _get_trial_id_key(self):
        document_meta = {'experiment_id': self.experiment_id,
                         'category': 'trial_id'}
        return MongoKey(document_meta)

    def _get_parameter_key(self, trial_id):
        document_meta = {'experiment_id': self.experiment_id,
                         'category': 'trial',
                         'trial_id': trial_id}
        return MongoKey(document_meta, field_name='parameter')

    def _get_history_key(self, trial_id):
        document_meta = {'experiment_id': self.experiment_id,
                         'category': 'trial',
                         'trial_id': trial_id}
        return MongoKey(document_meta, field_name='history')

    def _get_metric_key(self, metric_key, trial_id):
        document_meta = {'experiment_id': self.experiment_id,
                         'category': 'metric',
                         'metric_key': metric_key,
                         'trial_id': trial_id}
        return MongoKey(document_meta)

    def _get_persist_key(self, step, trial_id):
        document_meta = {'experiment_id': self.experiment_id,
                         'category': 'persist',
                         'step': step,
                         'trial_id': trial_id}
        return MongoKey(document_meta)

    def _get_step_hash_key(self, key):
        document_meta = {'experiment_id': self.experiment_id,
                         'category': 'step_hash',
                         'input_hash': key}
        return MongoKey(document_meta)

    def _get_code_key(self, trial_id):
        document_meta = {'experiment_id': self.experiment_id,
                         'category': 'code',
                         'trial_id': trial_id}
        return MongoKey(document_meta)

    def _get_environment_key(self, env_key, trial_id, ext):
        # ext is used in LocalBackend
        document_meta = {'experiment_id': self.experiment_id,
                         'category': 'environment',
                         'trial_id': trial_id}
        return MongoKey(document_meta, field_name=env_key)

    ################################################
    # Low level API
    ################################################

    def set(self, key, value):
        self._validate_key(key)
        return self.collection.update_one(key.document_meta,
                                          {'$set': {key.field_name: value}},
                                          upsert=True)

    def get(self, key):
        self._validate_key(key)
        doc = self.collection.find_one(key.document_meta)

        try:
            return doc[key.field_name]
        except (KeyError, TypeError):
            # doc may be None
            return None

    def append_list(self, key, value):
        self._validate_key(key)
        res = self.collection.update_one(key.document_meta,
                                         {'$push': {key.field_name: value}},
                                         upsert=True)
        return res

    def get_list(self, key):
        res = self.get(key)
        if res is None:
            return []
        return res

    def increment(self, key):
        from pymongo import ReturnDocument
        self._validate_key(key)
        c = self.collection
        result = c.find_one_and_update(key.document_meta,
                                       {'$inc': {key.field_name: 1}},
                                       upsert=True,
                                       return_document=ReturnDocument.AFTER)
        return result[key.field_name]

    ################################################
    # High level API
    ################################################

    def _validate_key(self, key):
        # overwritten in MongoBackend to support MongoKey
        assert isinstance(key, MongoKey), key

    def _delete_cache(self):
        self.client.drop_database(self.dbname)
