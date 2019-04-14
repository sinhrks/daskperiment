import pathlib

from daskperiment.core.errors import TrialIDNotFoundError
import daskperiment.io.pickle as pickle
from daskperiment.util.log import get_logger


logger = get_logger(__name__)


def init_backend(experiment_id=None, backend=None):
    """
    Initialize backend from Experiment ID and protocol.

    Prameters
    ---------
    experiment_id: str
       Experiment id
    backend: str
       Backend identifier

    Returns
    -------
    Backend: backend
    """
    if issubclass(type(backend), _BaseBackend):
        return backend

    if experiment_id is None:
        msg = ('Experiment ID is not provided. This is only allowed '
               'in package testing (otherwise, it is a package bug)')
        logger.warning(msg)
        experiment_id = 'daskperiment_package_test'

    if backend == 'local':
        # LocalBackend
        dname = '{}'.format(experiment_id)
        from daskperiment.config import _CACHE_DIR
        backend = _CACHE_DIR / dname

    if maybe_redis(backend):
        from daskperiment.backend.redis import RedisBackend
        return RedisBackend(experiment_id, backend)
    elif maybe_mongo(backend):
        from daskperiment.backend.mongo import MongoBackend
        return MongoBackend(experiment_id, backend)
    elif isinstance(backend, pathlib.Path):
        from daskperiment.backend.local import LocalBackend
        return LocalBackend(experiment_id, backend)
    else:
        raise NotImplementedError(backend)


def maybe_redis(uri):
    """
    Check whether arg should be regarded as Redis

    Prameters
    ---------
    uri: obj
       Argument to be distinguished

    Returns
    -------
    bool: maybe_redis
    """
    try:
        import redis
    except ImportError:
        return False
    if isinstance(uri, redis.ConnectionPool):
        return True
    elif not isinstance(uri, str):
        return False
    protocols = ['redis://', 'rediss://', 'unix://']
    return any(uri.startswith(p) for p in protocols)


def maybe_mongo(uri):
    """
    Check whether arg should be regarded as MongoDB

    Prameters
    ---------
    uri: obj
       Argument to be distinguished

    Returns
    -------
    bool: maybe_mongo
    """
    # TODO: handle mongo db instance
    if not isinstance(uri, str):
        return False
    return uri.startswith('mongodb://')


class _BaseBackend(object):

    def __init__(self, experiment_id):
        self.experiment_id = experiment_id

    def save(self):
        """
        Save myself to specified location.

        Dababase-like backends do nothing because internal status are
        all saved during other operations.
        """
        # overridden in LocalBackend
        # other backends should be stateless
        return self

    def load(self):
        """
        Load myself from specified location.

        Dababase-like backends do nothing because internal status are
        all saved during other operations.
        """
        return self


class _NoSQLBackend(_BaseBackend):

    _SEP = ':'

    def __repr__(self):
        return "{}('{}')".format(self.__class__.__name__, self.uri)

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return False
        if self.experiment_id != other.experiment_id:
            return False
        if self.uri != other.uri:
            return False
        return True

    def __getstate__(self):
        state = {}
        state['experiment_id'] = self.experiment_id
        state['uri'] = self.uri
        # do not pickle _client
        return state

    @property
    def client(self):
        raise NotImplementedError

    ################################################
    # Managers
    ################################################

    @property
    def metrics(self):
        if not hasattr(self, '_metrics'):
            from daskperiment.core.metric.nosql import NoSQLMetricManager
            self._metrics = NoSQLMetricManager(backend=self)
        return self._metrics

    @property
    def trials(self):
        if not hasattr(self, '_trials'):
            from daskperiment.core.trial import NoSQLTrialManager
            self._trials = NoSQLTrialManager(backend=self)
        return self._trials

    ################################################
    # Key management
    ################################################

    def build_key(self, *keys):
        keys = [str(key) for key in keys]
        return self._SEP.join(keys)

    def get_parameter_key(self, trial_id):
        return self.build_key(self.experiment_id, 'parameter', trial_id)

    def get_history_key(self, trial_id):
        return self.build_key(self.experiment_id, 'history', trial_id)

    def get_metric_key(self, metric_key, trial_id):
        return self.build_key(self.experiment_id, 'metric',
                              metric_key, trial_id)

    def get_persist_key(self, step, trial_id):
        """
        Get key to save persisted results
        """
        return self.build_key(self.experiment_id, 'persist', step, trial_id)

    def get_step_hash_key(self, key):
        """
        Get key to save persisted results
        """
        return self.build_key(self.experiment_id, 'step_hash', key)

    def get_code_key(self, trial_id):
        """
        Get key to save code
        """
        return self.build_key(self.experiment_id, 'code', trial_id)

    def get_environment_key(self, env_key, trial_id, ext):
        # ext is used in LocalBackend
        return self.build_key(self.experiment_id, env_key, trial_id)

    def get_trial_id_from_key(self, key):
        assert isinstance(key, (str, bytes)), key
        if isinstance(key, str):
            key = key.rsplit(self._SEP)[-1]
        else:
            key = key.rsplit(self._SEP.encode())[-1]
        return int(key)

    ################################################
    # Low level API
    ################################################

    def set(self, key, value):
        """
        This method must be overwritten by actual class
        """
        raise NotImplementedError

    def get(self, key):
        """
        This method must be overwritten by actual class
        """
        raise NotImplementedError

    def keys(self, key):
        """
        This method must be overwritten by actual class
        """
        return self.client.keys(key)

    def append_list(self, key, value):
        """
        This method must be overwritten by actual class
        """
        raise NotImplementedError

    def get_list(self, key):
        """
        This method must be overwritten by actual class
        """
        raise NotImplementedError

    def increment(self, key):
        """
        This method must be overwritten by actual class
        """
        raise NotImplementedError

    ################################################
    # High level API
    ################################################

    def save_text(self, key, text):
        assert isinstance(key, (str, bytes))
        return self.set(key, text)

    def load_text(self, key):
        """
        Load code context from file
        """
        assert isinstance(key, (str, bytes)), key
        res = self.client.get(key)

        if res is None:
            # TODO: define better exception
            # key may not contain trial id
            raise TrialIDNotFoundError(key)
        else:
            return res.decode('utf-8')

    def save_object(self, key, obj):
        """
        Save object to key
        """
        assert isinstance(key, (str, bytes)), key
        return self.set(key, pickle.dumps(obj))

    def load_object(self, key):
        """
        Load object from key
        """
        assert isinstance(key, (str, bytes)), key
        res = self.get(key)

        if res is None:
            raise TrialIDNotFoundError(key)
        else:
            return pickle.loads(res)
