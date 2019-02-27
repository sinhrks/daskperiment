from .base import ParallelExperimentBase
from daskperiment.testing import ex       # noqa


class TestParallelLocalExperiment(ParallelExperimentBase):

    backend = 'local'
