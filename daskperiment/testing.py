import pytest

import os

import daskperiment


IS_TRAVIS = "TRAVIS" in os.environ and os.environ["TRAVIS"] == "true"


@pytest.fixture
def ex(request):
    """
    Initialize and cleanup Experiment
    """
    name = request.function.__name__
    backend = request.cls.backend

    ex = daskperiment.Experiment(id=name, backend=backend)
    yield ex
    ex._delete_cache()


class CleanupMixin(object):

    def setup_class(cls):
        from daskperiment.backend import init_backend
        init_backend('remove_all', backend=cls.backend)._delete_cache()

    def teardown_class(cls):
        from daskperiment.backend import init_backend
        init_backend('remove_all', backend=cls.backend)._delete_cache()
