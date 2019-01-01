import pathlib

from daskperiment.backend.base import _BaseBackend
from daskperiment.core.errors import TrialIDNotFoundError
import daskperiment.io.pickle as pickle
from daskperiment.util.log import get_logger


logger = get_logger(__name__)


class LocalBackend(_BaseBackend):

    def __init__(self, experiment_id, cache_dir):
        self.experient_id = experiment_id
        self.cache_dir = cache_dir
        self.initialize_backend()

        from daskperiment.core.metric.local import LocalMetricManager
        self.metrics = LocalMetricManager(self.cache_dir)

        from daskperiment.core.trial import LocalTrialManager
        self.trials = LocalTrialManager(experiment_id, backend=self)

    def initialize_backend(self):
        pickle.maybe_create_dir('cache', self.cache_dir)

        # do not output INFO logs child folders
        pickle.maybe_create_dir('code', self.code_dir, info=False)
        pickle.maybe_create_dir('environment', self.environment_dir,
                                info=False)
        pickle.maybe_create_dir('persist', self.persist_dir, info=False)

    @property
    def code_dir(self):
        return self.cache_dir / 'code'

    @property
    def environment_dir(self):
        return self.cache_dir / 'environment'

    @property
    def persist_dir(self):
        return self.cache_dir / 'persist'

    def get_persist_key(self, experiment_id, step, trial_id):
        """
        Get Path instance to save persisted results
        """
        fname = '{}_{}_{}.pkl'.format(experiment_id, step, trial_id)
        return self.persist_dir / fname

    def get_code_key(self, experiment_id, trial_id):
        """
        Get Path instance to save code
        """
        fname = '{}_{}.py'.format(experiment_id, trial_id)
        return self.code_dir / fname

    def get_python_package_key(self, experiment_id, trial_id):
        fname = 'requirements_{}_{}.txt'.format(experiment_id, trial_id)
        path = self.environment_dir / fname
        return path

    def get_device_info_key(self, experiment_id, trial_id):
        fname = 'device_{}_{}.txt'.format(experiment_id, trial_id)
        path = self.environment_dir / fname
        return path

    def save_text(self, key, text):
        """
        Save text to key (pathlib.Path)
        """
        assert isinstance(key, pathlib.Path)
        key.write_text(text)

    def load_text(self, key):
        """
        Load text from key (pathlib.Path)
        """
        assert isinstance(key, pathlib.Path)
        try:
            return key.read_text()
        except FileNotFoundError:
            raise TrialIDNotFoundError(key)

    def save_object(self, key, obj):
        """
        Save object to key (pathlib.Path)
        """
        assert isinstance(key, pathlib.Path)
        pickle.save(obj, key)

    def load_object(self, key):
        """
        Load object from key (pathlib.Path)
        """
        assert isinstance(key, pathlib.Path)
        try:
            return pickle.load(key)
        except FileNotFoundError:
            raise TrialIDNotFoundError(key)

    def save(self, experiment_id):
        fname = '{}.pkl'.format(experiment_id)
        path = self.cache_dir / fname
        pickle.save(self, path)
        return self

    def load(self, experiment_id):
        fname = '{}.pkl'.format(experiment_id)
        path = self.cache_dir / fname
        if path.is_file():
            return pickle.load(path)
        else:
            return self

    def _delete_cache(self):
        """
        Delete cache dir
        """
        import shutil
        try:
            shutil.rmtree(self.cache_dir)
        except FileNotFoundError:
            pass
