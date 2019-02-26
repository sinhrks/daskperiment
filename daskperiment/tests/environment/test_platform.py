from daskperiment.environment.platform import (PlatformEnvironment,
                                               DetailedCPUEnvironment)


class TestPlatformEnvironment(object):

    def test_platform(self):
        env1 = PlatformEnvironment()
        env2 = PlatformEnvironment()

        assert env1 == env2

        env2.cpu_count = 100
        assert env1 != env2

    def test_platform_dict(self):
        env = PlatformEnvironment()
        exp = {'Platform Information': env.platform,
               'Device CPU Count': env.cpu_count}
        assert env.__json__() == exp

    def test_platform_roundtrip(self):
        env = PlatformEnvironment()
        res = env.loads(env.dumps())
        assert env is not res
        assert env == res

    def test_difference(self):
        env1 = PlatformEnvironment()
        env2 = PlatformEnvironment()

        env1.cpu_count = 2
        env2.cpu_count = 4

        res = env2.difference_from(env1)
        exp = ['@@ -2 +2 @@\n',
               '-Device CPU Count: 2',
               '+Device CPU Count: 4']
        assert res == exp


class TestDetailedCPUEnvironment(object):

    def test_eq(self):
        env1 = DetailedCPUEnvironment()
        env2 = DetailedCPUEnvironment()
        assert env1 == env2

        env2.vendor_id = 'dummy vendor'
        assert env1 != env2

    def test_content(self):
        e = DetailedCPUEnvironment()
        res = e.output_detail().splitlines()
        assert any('Hz Advertised Raw:' in r for r in res)

    def test_cpu_roundtrip(self):
        env = DetailedCPUEnvironment()
        res = env.loads(env.dumps())
        assert env is not res
        assert env == res

    def test_difference(self):
        env1 = DetailedCPUEnvironment()
        env2 = DetailedCPUEnvironment()

        env1.vendor_id = 'dummy1'
        env2.vendor_id = 'dummy2'

        res = env2.difference_from(env1)
        print(res)
        exp = ['@@ -3 +3 @@\n',
               '-Vendor ID: dummy1',
               '+Vendor ID: dummy2']
        assert res == exp

        env1.arch = 'dummy_arch1'
        env2.arch = 'dummy_arch2'

        res = env2.difference_from(env1)
        exp = ['@@ -3 +3 @@\n',
               '-Vendor ID: dummy1',
               '+Vendor ID: dummy2',
               '@@ -10 +10 @@\n',
               '-Arch: dummy_arch1',
               '+Arch: dummy_arch2']
        assert res == exp
