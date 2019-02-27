import os

from daskperiment.backend import init_backend
from daskperiment.core.errors import TrialIDNotFoundError
from daskperiment.environment.platform import (PlatformEnvironment,
                                               DetailedCPUEnvironment)
from daskperiment.environment.python import (PythonEnvironment,
                                             PythonPackagesEnvironment,
                                             NumPyEnvironment,
                                             SciPyEnvironment,
                                             PandasEnvironment,
                                             CondaEnvironment)
from daskperiment.environment.git import GitEnvironment
from daskperiment.util.log import get_logger


logger = get_logger(__name__)


class Environment(object):

    def __init__(self, backend):
        self.backend = init_backend(backend=backend)

        self.python = PythonEnvironment()
        self.python_packages = PythonPackagesEnvironment()

        self.collectors = [PlatformEnvironment(),
                           DetailedCPUEnvironment(),
                           self.python,
                           NumPyEnvironment(),
                           SciPyEnvironment(),
                           PandasEnvironment(),
                           CondaEnvironment(),
                           GitEnvironment(),
                           self.python_packages]
        self.mapping = {env.key: env for env in self.collectors}

    def keys(self):
        return [env.key for env in self.collectors]

    def log_environment_info(self):
        for env in self.collectors:
            for line in env.output_init():
                logger.info(line)

    def _load_single_environment(self, env, trial_id):
        """
        Load single environment instance
        """
        if trial_id is None:
            return env

        key = self.backend.get_environment_key(env.key, trial_id, env.ext)
        try:
            text = self.backend.load_text(key)
        except TrialIDNotFoundError:
            # overwrite message using trial_id
            raise TrialIDNotFoundError(trial_id)
        return env.loads(text)

    def check_environment_change(self, trial_id):
        for env in self.collectors:
            try:
                prev = self._load_single_environment(env, trial_id)
            except TrialIDNotFoundError:
                # file or db row may be deleted
                msg = ('Unable to load saved environment, '
                       'comparison is skipped: '
                       '(key: {}, trial id: {})')
                logger.error(msg.format(env.key, trial_id))
                continue

            diff = env.difference_from(prev)
            if diff is not None:
                msg = "Environment information has been changed: {}"
                logger.warning(msg.format(env.key))
                for d in diff:
                    logger.warning(d)

    def get_python_mode(self):
        return self.python.get_python_mode()

    def maybe_file(self):
        return self.python.maybe_file()

    def maybe_jupyter(self):
        return self.python.maybe_jupyter()

    def save(self, trial_id):
        for env in self.collectors:
            key = self.backend.get_environment_key(env.key, trial_id, env.ext)
            logger.debug('Saving {} info: {}'.format(env.key, key))
            self.backend.save_text(key, env.dumps())

    def get_environment(self, trial_id=None, category=None):
        if category is None:
            # compat for previous behaviour
            envs = [self.mapping['platform'],
                    self.mapping['python'],
                    self.mapping['git']]
            envs = [self._load_single_environment(e, trial_id=trial_id)
                    for e in envs]
            lines = [os.linesep.join(e.output_init()) for e in envs]
            return os.linesep.join(lines)
        else:
            category = str(category).lower()

            try:
                env = self.mapping[category]
            except KeyError:
                msg = 'Category must be either {}, given: {}'
                msg = msg.format(','.format(self.mapping.keys()), category)
                raise ValueError(msg)

            try:
                env = self._load_single_environment(env, trial_id)
            except TrialIDNotFoundError:
                msg = ('Unable to load saved environment: '
                       '(key: {}, trial id: {})')
                logger.error(msg.format(env.key, trial_id))
                raise
            return env.output_detail()

    def get_python_packages(self, trial_id=None):
        # TODO: deprecate?
        return self.get_environment(trial_id=trial_id,
                                    category='requirements')
