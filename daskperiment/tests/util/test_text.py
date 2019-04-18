import pytest

import os

from daskperiment.util.text import validate_identifier, trim_indent


class TestText(object):

    @pytest.mark.parametrize("key", ['xxx1', "aaa_aaa"])
    def test_validate_identifier(self, key):
        validate_identifier(key)

    @pytest.mark.parametrize("key", ['1xxx', 1, 'aaa.aaa', 'aaa:aaa',
                                     'aaa-aaa'])
    def test_validate_identifier_raises(self, key):
        with pytest.raises(ValueError):
            validate_identifier(key)

    def test_trim_indent(self):
        res = trim_indent("")
        assert res == ""

        res = trim_indent("ab")
        assert res == "ab"

        res = trim_indent(os.linesep)
        assert res == os.linesep

    def test_trim_multi(self):
        res = trim_indent("""
aaa""")
        assert res == """
aaa"""

        res = trim_indent(""" aaa
 aaa""")
        assert res == """aaa
aaa"""

        res = trim_indent(""" aaa


 aaa""")
        assert res == """aaa


aaa"""

        res = trim_indent("""    aaa
        aaa""")
        assert res == """aaa
    aaa"""

    def test_trim_multi_endsep(self):
        res = trim_indent("""
aaa
""")
        assert res == """
aaa
"""

        res = trim_indent(""" aaa
 aaa
""")
        assert res == """aaa
aaa
"""

        res = trim_indent("""    aaa
        aaa
""")
        assert res == """aaa
    aaa
"""

    def test_trim_multi_blankline(self):
        res = trim_indent("""    aaaa
a
aa
aaa
aaaa
aaaaa
""")
        assert res == """aaaa




a
"""
