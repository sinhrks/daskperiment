import multiprocessing
import os
import pathlib
import platform

from daskperiment.backend import init_backend
from daskperiment.core.errors import TrialIDNotFoundError
from daskperiment.util.diff import unified_diff
from daskperiment.util.git import maybe_git_repo
from daskperiment.util.log import get_logger

logger = get_logger(__name__)


class Environment(object):

    def __init__(self, backend):
        self.backend = init_backend(backend=backend)

        self.platform = PlatformEnvironment()
        self.python = PythonEnvironment()
        self.git = GitEnvironment()

        # list
        self.python_packages = self.get_python_packages()

    def log_environment_info(self):
        for env in [self.platform, self.python, self.git]:
            for line in env.format_list():
                logger.info(line)

        msg = "Number of installed Python packages: {}"
        logger.info(msg.format(len(self.python_packages)))

    def check_environment_change(self, trial_id):
        current = self.get_environment()
        previous = self.get_environment(trial_id=trial_id)

        if current != previous:
            msg = 'Environment has been changed'
            logger.warning(msg)
            for d in unified_diff(previous, current, n=0):
                logger.warning(d)
        else:
            logger.debug("Environment is not changed")

    def check_python_packages_change(self, trial_id):
        current = self.get_python_packages()
        previous = self.get_python_packages(trial_id=trial_id)

        if current != previous:
            msg = 'Installed Python packages have been changed'
            logger.warning(msg)
            for d in unified_diff(previous, current, n=0):
                logger.warning(d)
        else:
            logger.debug("Installed Python packages are not changed")

    def get_python_mode(self):
        return self.python.get_python_mode()

    def maybe_file(self):
        return self.python.shell == 'File'

    def maybe_jupyter(self):
        return self.python.shell == 'Jupyter Notebook'

    def _get_python_packages(self):
        import pkg_resources
        return pkg_resources.working_set

    def save(self, trial_id):
        self.save_environment(trial_id)
        self.save_python_packages(trial_id)

    def save_environment(self, trial_id):
        key = self.backend.get_platform_info_key(trial_id)
        logger.info('Saving platform info: {}'.format(key))
        self.backend.save_text(key, self.platform.dumps())

        key = self.backend.get_python_info_key(trial_id)
        logger.info('Saving Python info: {}'.format(key))
        self.backend.save_text(key, self.python.dumps())

        key = self.backend.get_git_info_key(trial_id)
        logger.info('Saving Git info: {}'.format(key))
        self.backend.save_text(key, self.git.dumps())

    def _get_environments(self, trial_id=None):
        if trial_id is None:
            return self.platform, self.python, self.git

        key = self.backend.get_platform_info_key(trial_id)
        text = self.backend.load_text(key)
        platform = self.platform.loads(text)

        key = self.backend.get_python_info_key(trial_id)
        text = self.backend.load_text(key)
        python = self.python.loads(text)

        key = self.backend.get_git_info_key(trial_id)
        text = self.backend.load_text(key)
        git = self.git.loads(text)
        return platform, python, git

    def get_environment(self, trial_id=None):
        info = self._get_environments(trial_id=trial_id)

        assert len(info) == 3
        return os.linesep.join(info[0].format_list() + info[1].format_list() +
                               info[2].format_list())

    def save_python_packages(self, trial_id):
        key = self.backend.get_python_package_key(trial_id)
        msg = 'Saving python packages: {}'
        logger.info(msg.format(key))

        text = self.get_python_packages()
        self.backend.save_text(key, text)

    def get_python_packages(self, trial_id=None):
        if trial_id is None:
            pkgs = ["{}=={}".format(p.project_name, p.version)
                    for p in self._get_python_packages()]
            return os.linesep.join(pkgs)
        else:
            key = self.backend.get_python_package_key(trial_id)
            try:
                return self.backend.load_text(key)
            except TrialIDNotFoundError:
                # overwrite message using trial_id
                raise TrialIDNotFoundError(trial_id)


class _EnvironmentObject(object):

    __slots__ = ()

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return False
        for key in self.__slots__:
            if getattr(self, key) != getattr(other, key):
                return False
        return True

    def format_list(self):
        """
        Convert to a list of string repr
        """
        res = []
        for key in self.__slots__:
            disp = getattr(self, '_{}'.format(key.upper()))
            res.append('{}: {}'.format(disp, getattr(self, key)))
        return res

    def __json__(self):
        """
        Dump myself
        """
        results = {}
        for attr in self.__slots__:
            key = getattr(self, '_{}'.format(attr.upper()))
            value = getattr(self, attr)
            assert isinstance(value, (int, float, str)), (key, value)
            results[key] = getattr(self, attr)
        return results

    def dumps(self):
        """
        Dump instance to JSON string
        """
        # use standard json not to parse datetime-like str
        import json
        return json.dumps(self.__json__())

    def loads(self, text):
        """
        Load instance from JSON string
        """
        # use standard json not to parse datetime-like str
        import json

        obj = object.__new__(self.__class__)

        attrs = json.loads(text)
        for k, v in attrs.items():
            # search slots which has the same repr
            for s in self.__slots__:
                key = getattr(self, '_{}'.format(s.upper()))
                if key == k:
                    setattr(obj, s, v)
        return obj


class PlatformEnvironment(_EnvironmentObject):
    """
    Handle device info

    * CPU
    * OS
    """
    __slots__ = ('platform', 'cpu_count')

    # class attribute for display key
    # should be capital with the same name
    _PLATFORM = 'Platform Information'
    _CPU_COUNT = 'Device CPU Count'

    def __init__(self):
        self.platform = platform.platform()
        self.cpu_count = multiprocessing.cpu_count()


class PythonEnvironment(_EnvironmentObject):
    """
    Handle Python info
    """
    __slots__ = ('implementation', 'version', 'shell',
                 'daskperiment_version', 'daskperiment_path')

    _IMPLEMENTATION = 'Python Implementation'
    _VERSION = 'Python Version'
    _SHELL = 'Python Shell Mode'

    _DASKPERIMENT_VERSION = 'Daskperiment Version'
    _DASKPERIMENT_PATH = 'Daskperiment Path'

    def __init__(self):
        self.implementation = platform.python_implementation()
        self.version = platform.python_version()

        # TODO: collect distribution

        self.shell = self.get_python_mode()

        # daskperiment info
        from daskperiment.version import version
        self.daskperiment_version = version
        p = pathlib.Path(__file__)
        self.daskperiment_path = str(p.parent.parent)

    def get_python_mode(self):
        # see https://stackoverflow.com/questions/15411967/
        try:
            shell = get_ipython().__class__.__name__
            if shell == 'ZMQInteractiveShell':
                return 'Jupyter Notebook'   # Jupyter notebook or qtconsole
            elif shell == 'TerminalInteractiveShell':
                return 'IPython Terminal'  # Terminal running IPython
            else:
                msg = 'Unable to detect python environment'
                raise RuntimeError(msg)
        except NameError:
            import __main__ as main
            if hasattr(main, '__file__'):
                if main.__file__.endswith('pytest'):
                    return 'Test'
                else:
                    return 'File'
            else:
                return 'Interactive Terminal'


class GitEnvironment(_EnvironmentObject):
    """
    Handle Git info

    * Git repo directory
    * Active branch
    """
    __slots__ = ('working_dir', 'repository', 'branch',
                 'commit')

    _WORKING_DIR = 'Working Directory'
    _REPOSITORY = 'Git Repository'
    _BRANCH = 'Git Active Branch'
    _COMMIT = 'Git HEAD Commit'

    def __init__(self):
        self.working_dir = str(pathlib.Path.cwd())

        repo = maybe_git_repo(os.getcwd())
        if repo is None:
            self.repository = 'Not Git Controlled'
            self.branch = 'Not Git Controlled'
            self.commit = 'Not Git Controlled'
        else:
            self.repository = repo.working_dir
            try:
                self.branch = repo.active_branch.name
            except TypeError:
                # If this symbolic reference is detached,
                # cannot retrieve active_branch
                self.branch = 'DETACHED'
            self.commit = repo.head.commit.hexsha
