import contextlib
import io
import os
import pathlib
import platform
import sys

import numpy as np
import pandas as pd

from daskperiment.environment.base import (_EnvironmentJsonDataClass,
                                           _EnvironmentTextDataClass)
from daskperiment.util.log import get_logger


logger = get_logger(__name__)


class PythonEnvironment(_EnvironmentJsonDataClass):
    """
    Handle Python info
    """
    key = 'python'

    __slots__ = ('implementation', 'version', 'shell',
                 'prefix', 'base_prefix', 'is_venv', 'venv_name',
                 'daskperiment_version', 'daskperiment_path')

    _IMPLEMENTATION = 'Python Implementation'
    _VERSION = 'Python Version'
    _SHELL = 'Python Shell Mode'

    _PREFIX = 'Python Prefix'
    _BASE_PREFIX = 'Python Base Prefix'
    _IS_VENV = 'Python venv Flag'
    _VENV_NAME = 'Python venv Name'

    _DASKPERIMENT_VERSION = 'Daskperiment Version'
    _DASKPERIMENT_PATH = 'Daskperiment Path'

    def __init__(self):
        self.implementation = platform.python_implementation()
        self.version = platform.python_version()

        self.shell = self.get_python_mode()

        self.prefix = sys.prefix
        self.base_prefix = sys.base_prefix
        self._detect_venv()

        # daskperiment info
        from daskperiment.version import version
        self.daskperiment_version = version
        p = pathlib.Path(__file__)
        self.daskperiment_path = str(p.parent.parent)

    def _detect_venv(self):
        """
        Update venv-related properties (for internal testing)
        """
        # https://docs.python.org/3.6/library/venv.html
        self.is_venv = (self.prefix != self.base_prefix)
        if self.is_venv:
            self.venv_name = os.path.basename(self.prefix)
        else:
            self.venv_name = ''

    def output_init(self):
        res = []
        for key in ['implementation', 'version', 'shell']:
            disp = getattr(self, '_{}'.format(key.upper()))
            res.append('{}: {}'.format(disp, getattr(self, key)))

        if self.is_venv:
            res.append('{}: {}'.format(self._VENV_NAME, self.venv_name))
        else:
            res.append('Python venv: False')

        for key in ['daskperiment_version']:
            disp = getattr(self, '_{}'.format(key.upper()))
            res.append('{}: {}'.format(disp, getattr(self, key)))
        return res

    def get_python_mode(self):
        # see https://stackoverflow.com/questions/15411967/
        try:
            shell = get_ipython().__class__.__name__
            if shell == 'ZMQInteractiveShell':
                # Jupyter notebook or qtconsole
                return 'Jupyter Notebook'
            elif shell == 'TerminalInteractiveShell':
                # Terminal running IPython
                return 'IPython Terminal'
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
        return self.shell == 'File'

    def maybe_jupyter(self):
        return self.shell == 'Jupyter Notebook'


class PythonPackagesEnvironment(_EnvironmentTextDataClass):
    """
    Handle Python packages info
    """
    key = 'requirements'

    def __init__(self):
        self.value = self.get_python_packages()

    def output_init(self):
        msg = "Number of Installed Python Packages: {}"
        return [msg.format(len([p for p in self.packages]))]

    @property
    def packages(self):
        import pkg_resources
        return pkg_resources.working_set

    def get_python_packages(self, trial_id=None):
        pkgs = ["{}=={}".format(p.project_name, p.version)
                for p in self.packages]
        return os.linesep.join(pkgs)


##########################################################
# Specific packages
##########################################################


class _PackageEnvironment(_EnvironmentTextDataClass):
    """
    To dump package details (not shown in logs, but dumps as text)
    """
    def output_init(self):
        return []


class NumPyEnvironment(_PackageEnvironment):
    """
    Handle NumPy info
    """
    key = 'numpy'

    def __init__(self):
        self.value = self._CACHE

    @classmethod
    def cache_info(cls):
        f = io.StringIO()
        with contextlib.redirect_stdout(f):
            np.show_config()
        cls._CACHE = f.getvalue()


class SciPyEnvironment(_PackageEnvironment):
    """
    Handle SciPy info
    """
    key = 'scipy'

    def __init__(self):
        self.value = self._CACHE

    @classmethod
    def cache_info(cls):
        try:
            # scipy is not mandatory requirement
            import scipy
        except ImportError:
            cls._CACHE = 'SciPy is not installed'
            return

        f = io.StringIO()
        with contextlib.redirect_stdout(f):
            try:
                scipy.show_config()
            except Exception as e:
                msg = ('Unable to collect scipy related information, '
                       'scipy.show_config raises {}({})')
                logger.error(msg.format(e.__class__.__name__, e))

        cls._CACHE = f.getvalue()


class PandasEnvironment(_PackageEnvironment):
    """
    Handle pandas info
    """
    key = 'pandas'

    def __init__(self):
        self.value = self._CACHE

    @classmethod
    def cache_info(cls):
        f = io.StringIO()
        with contextlib.redirect_stdout(f):
            try:
                pd.show_versions()
            except Exception as e:
                msg = ('Unable to collect pandas related information, '
                       'pandas.show_versions raises {}({})')
                logger.error(msg.format(e.__class__.__name__, e))

        cls._CACHE = f.getvalue()


class CondaEnvironment(_PackageEnvironment):
    """
    Handle conda info
    """
    key = 'conda'

    def __init__(self):
        self.value = self._CACHE

    @classmethod
    def cache_info(cls):
        try:
            # conda is not mandatory requirement
            import conda
        except ImportError:
            cls._CACHE = 'conda is not installed'
            return

        try:
            import conda.cli.python_api
            cls._CACHE = conda.cli.python_api.run_command('info')[0]
        except Exception as e:
            msg = ('Unable to collect conda related information, '
                   'conda info raises {}({})')
            msg = msg.format(e.__class__.__name__, e)
            logger.error(msg)
            cls._CACHE = msg


NumPyEnvironment.cache_info()
SciPyEnvironment.cache_info()
PandasEnvironment.cache_info()
CondaEnvironment.cache_info()
