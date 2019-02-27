from .base import ExperimentBase
from daskperiment.testing import ex       # noqa


class TestLocalExperiment(ExperimentBase):

    backend = 'local'
