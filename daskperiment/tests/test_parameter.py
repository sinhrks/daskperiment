import pytest

import daskperiment


class TestParameter(object):

    def test_repr(self):
        ex = daskperiment.Experiment(id="test_repr")
        a = ex.parameter("a")
        assert repr(a) == "Parameter(a: Undefined)"

        b = ex.parameter("b")
        assert repr(b) == "Parameter(b: Undefined)"

        ex.set_parameters(a=1)
        assert repr(a) == "Parameter(a: 1<class 'int'>)"
        assert repr(b) == "Parameter(b: Undefined)"

    def test_compute(self):
        ex = daskperiment.Experiment(id="test_compute")
        a = ex.parameter("a")

        with pytest.raises(daskperiment.core.errors.ParameterUndefinedError):
            a.compute()

        ex.set_parameters(a=2)
        assert a.compute() == 2

        ex.set_parameters(a=3)
        assert a.compute() == 3

    def test_operator(self):
        ex = daskperiment.Experiment(id="test_operator")
        a = ex.parameter("a")

        ex.set_parameters(a=2)
        assert (a + 1).compute() == 3
        assert (1 + a + 3).compute() == 6

        ex.set_parameters(a=5)
        assert (a + 1).compute() == 6
        assert (1 + a + 3).compute() == 9
