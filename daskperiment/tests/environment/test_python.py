import os
import pkg_resources

from daskperiment.environment.python import (PythonEnvironment,
                                             PythonPackagesEnvironment,
                                             NumPyEnvironment,
                                             SciPyEnvironment,
                                             PandasEnvironment,
                                             CondaEnvironment)


class TestPythonEnvironment(object):

    def test_python(self):
        env1 = PythonEnvironment()
        env2 = PythonEnvironment()

        assert env1 == env2

        env2.version = 'dummy_version'
        assert env1 != env2

    def test_python_dict(self):
        env = PythonEnvironment()
        exp = {'Python Implementation': env.implementation,
               'Python Version': env.version,
               'Python Shell Mode': env.shell,
               'Python Prefix': env.prefix,
               'Python Base Prefix': env.base_prefix,
               'Python venv Flag': env.is_venv,
               'Python venv Name': env.venv_name,
               'Daskperiment Version': env.daskperiment_version,
               'Daskperiment Path': env.daskperiment_path}
        assert env.__json__() == exp

    def test_python_roundtrip(self):
        env = PythonEnvironment()
        res = env.loads(env.dumps())
        assert env is not res
        assert env == res

    def test_difference(self):
        env1 = PythonEnvironment()
        env2 = PythonEnvironment()

        env1.version = '3.6.0'
        env2.version = '3.7.0'

        res = env2.difference_from(env1)
        exp = ['@@ -2 +2 @@\n',
               '-Python Version: 3.6.0',
               '+Python Version: 3.7.0']
        assert res == exp

    def test_not_venv(self):
        env = PythonEnvironment()

        assert not env.is_venv
        assert env.venv_name == ''

        exp = ['Python Implementation: {}'.format(env.implementation),
               'Python Version: {}'.format(env.version),
               'Python Shell Mode: {}'.format(env.shell),
               'Python venv: False',
               'Daskperiment Version: {}'.format(env.daskperiment_version)]
        assert env.output_init() == exp

    def test_venv(self):
        env = PythonEnvironment()
        env.prefix = os.path.join(os.getcwd(), 'myenv')
        env._detect_venv()

        assert env.is_venv
        assert env.venv_name == 'myenv'

        exp = ['Python Implementation: {}'.format(env.implementation),
               'Python Version: {}'.format(env.version),
               'Python Shell Mode: {}'.format(env.shell),
               'Python venv Name: myenv',
               'Daskperiment Version: {}'.format(env.daskperiment_version)]
        assert env.output_init() == exp

    def test_venv_roundtrip(self):
        env = PythonEnvironment()
        env.prefix = os.path.join(os.getcwd(), 'myenv')
        env._detect_venv()

        assert env.is_venv
        assert env.venv_name == 'myenv'

        res = env.loads(env.dumps())
        assert env is not res
        assert env == res


class TestPythonPackagesEnvironment(object):

    def test_eq(self):
        env1 = PythonPackagesEnvironment()
        env2 = PythonPackagesEnvironment()
        assert env1 == env2

        env2.value += 'xx'
        assert env1 != env2

    def test_python_packages(self):
        e = PythonPackagesEnvironment()
        assert any(r.startswith('pandas==') for r in e.value.splitlines())

    def test_output_init(self):
        e = PythonPackagesEnvironment()
        length = len([p for p in pkg_resources.working_set])

        exp = "Number of Installed Python Packages: {}".format(length)
        assert e.output_init() == [exp]

    def test_pythonpackages_roundtrip(self):
        env = PythonPackagesEnvironment()
        res = env.loads(env.dumps())
        assert env is not res
        assert env == res

    def test_difference(self):
        env1 = PythonPackagesEnvironment()
        env2 = PythonPackagesEnvironment()

        lines = env1.value.splitlines()
        lines[2] = 'dummy_pkg==0.1'
        env1.value = os.linesep.join(lines)

        lines = env2.value.splitlines()
        lines[2] = 'dummy_pkg==0.2'
        env2.value = os.linesep.join(lines)

        res = env2.difference_from(env1)
        exp = ['@@ -3 +3 @@\n',
               '-dummy_pkg==0.1',
               '+dummy_pkg==0.2']
        assert res == exp

        lines = env1.value.splitlines()
        lines[0] = 'dummy_pkg2==0.1'
        env1.value = os.linesep.join(lines)

        lines = env2.value.splitlines()
        lines[0] = 'dummy_pkg2==0.2'
        env2.value = os.linesep.join(lines)

        res = env2.difference_from(env1)
        exp = ['@@ -1 +1 @@\n',
               '-dummy_pkg2==0.1',
               '+dummy_pkg2==0.2',
               '@@ -3 +3 @@\n',
               '-dummy_pkg==0.1',
               '+dummy_pkg==0.2']
        assert res == exp


class PackageBase(object):

    def test_eq(self):
        env1 = self.klass()
        env2 = self.klass()
        assert env1 == env2

        assert len(env1.value.splitlines()) > 5

        lines = env1.value.splitlines()
        lines[2] = 'modified'
        env1.value = os.linesep.join(lines)
        assert env1 != env2

    def test_roundtrip(self):
        env = self.klass()
        res = env.loads(env.dumps())
        assert env is not res
        assert env == res

    def test_difference(self):
        env1 = self.klass()
        env2 = self.klass()

        lines = env1.value.splitlines()
        lines[2] = 'dummy_descr'
        env1.value = os.linesep.join(lines)

        lines = env2.value.splitlines()
        lines[2] = 'updated_descr'
        env2.value = os.linesep.join(lines)

        res = env2.difference_from(env1)
        exp = ['@@ -3 +3 @@\n',
               '-dummy_descr',
               '+updated_descr']
        assert res == exp

        lines = env1.value.splitlines()
        lines[0] = 'dummy_descr2'
        env1.value = os.linesep.join(lines)

        lines = env2.value.splitlines()
        lines[0] = 'updated_descr2'
        env2.value = os.linesep.join(lines)

        res = env2.difference_from(env1)
        exp = ['@@ -1 +1 @@\n',
               '-dummy_descr2',
               '+updated_descr2',
               '@@ -3 +3 @@\n',
               '-dummy_descr',
               '+updated_descr']
        assert res == exp


class TestNumPyEnvironment(PackageBase):

    klass = NumPyEnvironment

    def test_content(self):
        e = self.klass()
        assert any(r.startswith('blas_mkl_info:')
                   for r in e.value.splitlines())


class TestSciPyEnvironment(PackageBase):

    klass = SciPyEnvironment

    def test_content(self):
        e = self.klass()
        assert any(r.startswith('openblas_info:')
                   for r in e.value.splitlines())


class TestPandasEnvironment(object):

    klass = PandasEnvironment

    def test_content(self):
        e = self.klass()
        assert any(r.startswith('INSTALLED VERSIONS')
                   for r in e.value.splitlines())


class TestCondaEnvironment(object):

    klass = CondaEnvironment

    def test_content(self):
        e = self.klass()
        assert any('conda version' in r
                   for r in e.value.splitlines())
