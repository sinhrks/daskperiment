import inspect
import os

from daskperiment.core.code import CodeManager
from daskperiment.util.diff import unified_diff


class TestCodeManager(object):

    def test_describe(self):
        c = CodeManager()

        def a(x, y):
            return 0

        c.register(a)
        exp = """        def a(x, y):
            return 0
"""
        assert c.describe() == exp

        def b(x, y, z):
            return 15

        c.register(b)
        exp = """        def a(x, y):
            return 0


        def b(x, y, z):
            return 15
"""
        assert c.describe() == exp

    def test_copy(self):
        c = CodeManager()

        def a(x, y):
            return 0

        def b(x, y, z):
            return 15

        c.register(a)
        c.register(b)

        n = c.copy()
        exp = """        def a(x, y):
            return 0


        def b(x, y, z):
            return 15
"""
        assert n.describe() == exp

        c = CodeManager()

        def a(x, y):
            return 0

        c.register(a)
        exp = """        def a(x, y):
            return 0
"""
        assert c.describe() == exp

        def b(x, y, z):
            return 15

        c.register(b)
        exp = """        def a(x, y):
            return 0


        def b(x, y, z):
            return 15
"""
        assert c.describe() == exp

    def test_code_diff(self):

        def inc(a):
            return a + 1
        s1 = inspect.getsource(inc)

        def inc(a):
            a = a + 1
            return a
        s2 = inspect.getsource(inc)

        res = os.linesep.join(unified_diff(s1, s2))
        exp = """@@ -1,2 +1,3 @@

         def inc(a):
-            return a + 1
+            a = a + 1
+            return a"""
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
