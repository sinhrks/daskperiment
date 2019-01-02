import inspect
import os

from daskperiment.core.code import CodeManager
from daskperiment.util.diff import unified_diff


class TestCodeManager(object):

    def test_describe(self):
        c = CodeManager('local')

        def a(x, y):
            return 0

        c.register(a)
        exp = """def a(x, y):
    return 0
"""
        assert c.describe() == exp

        def b(x, y, z):
            return 15

        c.register(b)
        exp = """def a(x, y):
    return 0


def b(x, y, z):
    return 15
"""
        assert c.describe() == exp

    def test_overwrite(self):
        c = CodeManager('local')

        def a(x, y):
            return 0

        def b(x, y, z):
            return 15

        c.register(a)
        c.register(b)

        exp = """def a(x, y):
    return 0


def b(x, y, z):
    return 15
"""
        assert c.describe() == exp

        def a(x, y):
            return 1

        c.register(a)

        exp = """def a(x, y):
    return 1


def b(x, y, z):
    return 15
"""
        assert c.describe() == exp

        def b(x, y, z):
            return 16

        c.register(b)

        exp = """def a(x, y):
    return 1


def b(x, y, z):
    return 16
"""
        assert c.describe() == exp

    def test_code_diff(self):
        c = CodeManager('local')

        def inc(a):
            return a + 1
        s1 = c._get_code_context(inc)

        def inc(a):
            a = a + 1
            return a
        s2 = c._get_code_context(inc)

        res = os.linesep.join(unified_diff(s1, s2))
        exp = """@@ -1,2 +1,3 @@

 def inc(a):
-    return a + 1
+    a = a + 1
+    return a"""
        assert res == exp

    def test_code_equiv(self):

        def inc(a):
            return a + 1
        s1 = inspect.getsource(inc)

        def inc(a):
            return a + 1
        s2 = inspect.getsource(inc)

        res = os.linesep.join(unified_diff(s1, s2))
        exp = ""
        assert res == exp


def gfunc(a, b):

    return a + b


class TestCodeContext(object):

    def test_code_context_global(self):
        c = CodeManager('local')

        res = c._get_code_context(gfunc)
        exp = """def gfunc(a, b):

    return a + b
"""
        assert res == exp

        def inc_line(a):

            return a + 1

        res = c._get_code_context(inc_line)
        exp = """def inc_line(a):

    return a + 1
"""
        assert res == exp

    def test_code_context(self):
        c = CodeManager('local')

        def inc(a):
            return a + 1

        res = c._get_code_context(inc)
        exp = """def inc(a):
    return a + 1
"""
        assert res == exp

        def inc_line(a):

            return a + 1

        res = c._get_code_context(inc_line)
        exp = """def inc_line(a):

    return a + 1
"""
        assert res == exp
