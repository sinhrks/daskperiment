import pytest

import daskperiment
from daskperiment.core.parameter import ParameterManager, Undefined


class TestUndefined(object):

    def test_repr(self):
        u = Undefined()
        assert repr(u) == 'Undefined'

    def test_eq(self):
        u1 = Undefined()
        u2 = Undefined()
        assert u1 == u2


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

        ex._delete_cache()

    def test_compute(self):
        ex = daskperiment.Experiment(id="test_compute")
        a = ex.parameter("a")

        with pytest.raises(daskperiment.core.errors.ParameterUndefinedError):
            a.compute()

        ex.set_parameters(a=2)
        assert a.compute() == 2

        ex.set_parameters(a=3)
        assert a.compute() == 3

        ex._delete_cache()

    def test_operator(self):
        ex = daskperiment.Experiment(id="test_operator")
        a = ex.parameter("a")

        ex.set_parameters(a=2)
        assert (a + 1).compute() == 3
        assert (1 + a + 3).compute() == 6

        ex.set_parameters(a=5)
        assert (a + 1).compute() == 6
        assert (1 + a + 3).compute() == 9

        ex._delete_cache()

    def test_parameter_manager(self):
        p = ParameterManager()
        p.define('a')
        p.define('b')

        assert p.describe() == "a=Undefined, b=Undefined"

        p.set(a=2)
        assert p.describe() == "a=2<class 'int'>, b=Undefined"

    def test_parameter_resolve(self):
        p = ParameterManager()
        a = p.define('a')
        b = p.define('b')

        p.set(a=2)
        assert a.resolve() == 2

        with pytest.raises(daskperiment.core.errors.ParameterUndefinedError):
            b.resolve()

        p.set(b=5)
        assert b.resolve() == 5

    def test_parameter_redefine(self):
        p = ParameterManager()

        a1 = p.define('a')
        assert p.describe() == "a=Undefined"
        a2 = p.define('a')
        assert p.describe() == "a=Undefined"

        with pytest.raises(daskperiment.core.errors.ParameterUndefinedError):
            a1.resolve()
        with pytest.raises(daskperiment.core.errors.ParameterUndefinedError):
            a2.resolve()

        p.set(a=2)
        assert p.describe() == "a=2<class 'int'>"
        assert a1.resolve() == 2
        assert a2.resolve() == 2

    def test_parameter_copy(self):
        p = ParameterManager()
        a = p.define('a')
        b = p.define('b')

        p.set(a=2, b=5)
        assert p.describe() == "a=2<class 'int'>, b=5<class 'int'>"
        assert a.resolve() == 2
        assert b.resolve() == 5

        n = p.copy()
        assert n.describe() == "a=2<class 'int'>, b=5<class 'int'>"

        assert a.resolve() == 2
        assert b.resolve() == 5

    def test_parameter_check_defined(self):
        p = ParameterManager()
        p.define('a')
        p.define('b')

        with pytest.raises(daskperiment.core.errors.ParameterUndefinedError):
            p._check_all_defined()

        p.set(a=2)
        with pytest.raises(daskperiment.core.errors.ParameterUndefinedError):
            p._check_all_defined()

        p.set(b=5)
        p._check_all_defined()

    def test_parameter_to_dict(self):
        p = ParameterManager()
        p.define('a')
        p.define('b')

        exp = {'a': Undefined(), 'b': Undefined()}
        assert p.to_dict() == exp

        p.set(a=1)
        exp = {'a': 1, 'b': Undefined()}
        assert p.to_dict() == exp
