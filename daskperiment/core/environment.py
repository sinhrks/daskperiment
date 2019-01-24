import pathlib
import platform

from daskperiment.util.log import get_logger

logger = get_logger(__name__)


class Environment(object):

    def __init__(self):
        logger.info(self.get_platform_info())
        logger.info(self.get_processor_info())
        logger.info(self.get_package_info())
        logger.info(self.get_cwd())

    def get_platform_info(self):
        return "Platform: {} {}".format(platform.system(), platform.release())

    def get_processor_info(self):
        return "Processor: {}".format(platform.processor())

    def get_package_info(self):
        p = pathlib.Path(__file__)
        return "Packagge path: {}".format(p.parent.parent)

    def get_cwd(self):
        return "Working directory: {}".format(pathlib.Path.cwd())
