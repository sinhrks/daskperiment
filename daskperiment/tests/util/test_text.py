import os
from daskperiment.util.text import trim_indent


class TestText(object):

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
