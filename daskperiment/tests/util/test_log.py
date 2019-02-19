import logging


class TestLogging(object):

    def test_log_level(self):
        logger = logging.getLogger('daskperiment')
        assert logger.getEffectiveLevel() == logging.INFO

        logger = logging.getLogger('daskperiment.core.experiment')
        assert logger.getEffectiveLevel() == logging.INFO

        # change child level
        logger.setLevel(logging.DEBUG)
        logger = logging.getLogger('daskperiment.core.experiment')
        assert logger.getEffectiveLevel() == logging.DEBUG
