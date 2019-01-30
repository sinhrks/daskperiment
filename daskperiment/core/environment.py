import os
import pathlib
import platform

from daskperiment.util.diff import unified_diff
from daskperiment.util.log import get_logger

logger = get_logger(__name__)


class Environment(object):

    def __init__(self):
        self.platform_info = platform.platform()
        self.python_info = "{} {}".format(platform.python_implementation(),
                                          platform.python_version())
        self.python_shell = self.get_python_mode()
        self.python_packages = self.get_python_packages()

    def check_diff(self, previous):
        """
        Check difference from previous Environment
        """
        assert isinstance(previous, Environment)

        # do not check python shell
        attrs = [('platform_info', 'platform'),
                 ('python_info', 'Python info')]
        for (attr_name, key) in attrs:
            try:
                self._assert_diff(previous, attr_name, key)
            except ValueError as e:
                for line in str(e).splitlines():
                    logger.warning(line)
        if self.python_packages != previous.python_packages:
            msg = 'Installed Python packages have been changed'
            logger.warning(msg)
            for d in unified_diff(previous.python_packages,
                                  self.python_packages, n=0):
                logger.warning(d)
        else:
            logger.debug("Installed Python packages are unchanged")

    def _assert_diff(self, previous, attr_name, key):
        current_attr = getattr(self, attr_name)
        assert isinstance(current_attr, str)
        previous_attr = getattr(previous, attr_name)
        assert isinstance(previous_attr, str)
        if current_attr != previous_attr:
            msg = """{cap_key} is changed
Previous {key}: {previous}
Current {key}: {current}""".format(cap_key=key.title(), key=key,
                                   previous=previous_attr,
                                   current=current_attr)
            raise ValueError(msg)
        else:
            logger.debug("{} is unchanged".format(key.title()))

    def describe(self):
        logger.info("Platform: {}".format(self.platform_info))
        logger.info("Python: {} ({})".format(self.python_info,
                                             self.python_shell))

        from daskperiment.version import version
        logger.info("daskperiment version: {}".format(version))
        p = pathlib.Path(__file__)
        logger.info("daskperiment path: {}".format(p.parent.parent))
        logger.info("Working directory: {}".format(pathlib.Path.cwd()))
        msg = "Number of installed Python packages: {}"
        logger.info(msg.format(len(self.python_packages)))

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
        return [repr(p) for p in self._get_python_packages()]

    def save_python_packages(self, path):
        """
        Save Python package info with pip freeze format
        """
        pkgs = self._get_pip_freeze()
        msg = 'Saving Python package info: {}'
        logger.info(msg.format(path))
        path.write_text(os.linesep.join(pkgs))

    def _get_pip_freeze(self):
        return ["{}=={}".format(p.project_name, p.version)
                for p in self._get_python_packages()]
