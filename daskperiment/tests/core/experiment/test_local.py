from .base import ExperimentBase


class TestLocalExperiment(ExperimentBase):

    @property
    def backend(self):
        return 'local'
