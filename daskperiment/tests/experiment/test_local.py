from daskperiment.tests.experiment.base import ExperimentBase


class TestLocalExperiment(ExperimentBase):

    @property
    def backend(self):
        return 'local'
