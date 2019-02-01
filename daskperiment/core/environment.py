import os
import pathlib
import platform

from daskperiment.backend import init_backend
from daskperiment.core.errors import TrialIDNotFoundError
from daskperiment.util.diff import unified_diff
from daskperiment.util.log import get_logger

logger = get_logger(__name__)


class Environment(object):

    def __init__(self, backend):
        self.backend = init_backend(backend=backend)

        self.platform_info = platform.platform()
        self.python_info = "{} {}".format(platform.python_implementation(),
                                          platform.python_version())
        self.python_shell = self.get_python_mode()
        self.python_packages = self.get_python_packages()

    def log_environment_info(self):
        for msg in self.get_device_info():
            logger.info(msg)

    def check_environment_change(self, previous):
        current = os.linesep.join(self.get_device_info())
        if current != previous:
            msg = 'Environment information has been changed'
            logger.warning(msg)
            for d in unified_diff(previous, current, n=0):
                logger.warning(d)
        else:
            logger.debug("Environment information is not changed")

    def check_python_packages_change(self, previous):
        current = os.linesep.join(self.get_python_packages())
        if current != previous:
            msg = 'Installed Python packages have been changed'
            logger.warning(msg)
            for d in unified_diff(previous, current, n=0):
                logger.warning(d)
        else:
            logger.debug("Installed Python packages are not changed")

    def get_device_info(self):
        from daskperiment.version import version
        p = pathlib.Path(__file__)
        msg = "Number of installed Python packages: {}"
        info = ["Platform: {}".format(self.platform_info),
                "Python: {} ({})".format(self.python_info,
                                         self.python_shell),
                "daskperiment version: {}".format(version),
                "daskperiment path: {}".format(p.parent.parent),
                "Working directory: {}".format(pathlib.Path.cwd()),
                msg.format(len(self.python_packages))]
        return info

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

    def maybe_file(self):
        return self.python_shell == 'File'

    def _get_python_packages(self):
        import pkg_resources
        return pkg_resources.working_set

    def get_python_packages(self):
        """
        Lists installed python packages
        """
        return ["{}=={}".format(p.project_name, p.version)
                for p in self._get_python_packages()]

    def save(self, trial_id):
        self.save_device_info(trial_id)
        self.save_python_packages(trial_id)

    def save_device_info(self, trial_id):
        key = self.backend.get_device_info_key(trial_id)
        msg = 'Saving device info: {}'
        logger.info(msg.format(key))

        text = os.linesep.join(self.get_device_info())
        self.backend.save_text(key, text)

    def load_device_info(self, trial_id):
        key = self.backend.get_device_info_key(trial_id)
        try:
            return self.backend.load_text(key)
        except TrialIDNotFoundError:
            # overwrite message using trial_id
            raise TrialIDNotFoundError(trial_id)

    def save_python_packages(self, trial_id):
        key = self.backend.get_python_package_key(trial_id)
        msg = 'Saving python packages: {}'
        logger.info(msg.format(key))

        text = os.linesep.join(self.get_python_packages())
        self.backend.save_text(key, text)

    def load_python_packages(self, trial_id):
        key = self.backend.get_python_package_key(trial_id)
        try:
            return self.backend.load_text(key)
        except TrialIDNotFoundError:
            # overwrite message using trial_id
            raise TrialIDNotFoundError(trial_id)
