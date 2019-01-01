import pytest

from daskperiment.core.parser import parse_parameter


class TestParser(object):

    def test_parse_parameter(self):
        lvalue, rvalue = parse_parameter('a=1')
        assert lvalue == 'a'
        assert rvalue == 1

        lvalue, rvalue = parse_parameter('a=1.1')
        assert lvalue == 'a'
        assert rvalue == 1.1

        lvalue, rvalue = parse_parameter('a_1="1.1"')
        assert lvalue == 'a_1'
        assert rvalue == "1.1"

    def test_parse_errors(self):
        with pytest.raises(SyntaxError):
            parse_parameter('a==1')

        with pytest.raises(SyntaxError):
            parse_parameter('a=1.1.1')

        with pytest.raises(SyntaxError):
            parse_parameter('a.1="1.1"')

        with pytest.raises(SyntaxError):
            parse_parameter('a')
