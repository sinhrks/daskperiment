import pathlib
import platform

from daskperiment.util.log import get_logger

logger = get_logger(__name__)


class Environment(object):

    def __init__(self):
        self.platform_info = platform.platform()
        self.python_info = "{} {}".format(platform.python_implementation(),
                                          platform.python_version())
        self.python_shell = self.get_python_mode()

    def describe(self):
        logger.info("Platform: {}".format(self.platform_info))
        logger.info("Python: {} ({})".format(self.python_info,
                                             self.python_shell))

        from daskperiment.version import version
        logger.info("daskperiment version: {}".format(version))
        p = pathlib.Path(__file__)
        logger.info("daskperiment path: {}".format(p.parent.parent))
        logger.info("Working directory: {}".format(pathlib.Path.cwd()))

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
