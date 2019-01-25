import pathlib
import platform

from daskperiment.util.log import get_logger

logger = get_logger(__name__)


class Environment(object):

    def __init__(self):
        logger.info(self.get_platform_info())
        logger.info(self.get_python_info())
        logger.info(self.get_package_version())
        logger.info(self.get_package_path())
        logger.info(self.get_cwd())

    def get_platform_info(self):
        return "Platform: {}".format(platform.platform())

    def get_python_info(self):
        return "Python: {} {}".format(platform.python_implementation(),
                                      platform.python_version())

    def get_package_version(self):
        from daskperiment.version import version
        return "daskperiment version: {}".format(version)

    def get_package_path(self):
        p = pathlib.Path(__file__)
        return "daskperiment path: {}".format(p.parent.parent)

    def get_cwd(self):
        return "Working directory: {}".format(pathlib.Path.cwd())
