import pytest

import subprocess
import sys

import daskperiment
import daskperiment.testing
from daskperiment.core.environment import (Environment,
                                           PlatformEnvironment,
                                           PythonEnvironment,
                                           GitEnvironment)


class TestEnvironment(object):

    def test_pip_packages(self):
        e = Environment('local')
        res = e.get_python_packages()
        assert any(r.startswith('pandas==') for r in res.splitlines())

    def test_environment(self):
        e = Environment('local')
        res = e.get_environment()

        lines = res.splitlines()
        assert len(lines) == 11

        assert lines[0].startswith('Platform Information:')
        assert lines[1].startswith('Device CPU Count:')
        assert lines[2].startswith('Python Implementation:')
        assert lines[3].startswith('Python Version:')
        assert lines[4].startswith('Python Shell Mode:')
        assert lines[5].startswith('Daskperiment Version:')
        assert lines[6].startswith('Daskperiment Path:')
        assert lines[7].startswith('Working Directory:')
        assert lines[8].startswith('Git Repository:')
        assert lines[9].startswith('Git Active Branch:')
        assert lines[10].startswith('Git HEAD Commit:')

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
               'Daskperiment Version': env.daskperiment_version,
               'Daskperiment Path': env.daskperiment_path}
        assert env.__json__() == exp

    def test_python_roundtrip(self):
        env = PythonEnvironment()
        res = env.loads(env.dumps())
        assert env is not res
        assert env == res

    def test_git(self):
        env1 = GitEnvironment()
        env2 = GitEnvironment()

        assert env1 == env2

        env2.branch = 'dummy_branch'
        assert env1 != env2

    def test_git_dict(self):
        env = GitEnvironment()
        exp = {'Working Directory': env.working_dir,
               'Git Repository': env.repository,
               'Git Active Branch': env.branch,
               'Git HEAD Commit': env.commit}
        assert env.__json__() == exp

    def test_git_roundtrip(self):
        env = GitEnvironment()
        res = env.loads(env.dumps())
        assert env is not res
        assert env == res


class TestPythonMode(object):

    def test_python_mode_test(self):
        e = Environment('local')
        assert e.get_python_mode() == 'Test'

    @pytest.mark.skipif(daskperiment.testing.IS_TRAVIS,
                        reason='skip on Travis CI')
    def test_python_mode_file(self):
        file = 'scripts/environment_check.py'

        p = subprocess.Popen([sys.executable, file], stdout=subprocess.PIPE)
        stdout, stderr = p.communicate()
        assert p.returncode == 0
        assert stdout == b'File\n'

    def test_python_mode_prompt(self, capsys):
        script = ('from daskperiment.core.environment import Environment;'
                  'e = Environment("local");'
                  'print(e.get_python_mode())')

        p = subprocess.Popen([sys.executable, '-c', script],
                             stdout=subprocess.PIPE)
        stdout, stderr = p.communicate()
        assert p.returncode == 0
        assert stdout == b'Interactive Terminal\n'
