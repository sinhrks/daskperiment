from daskperiment.core.code import CodeManager


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
