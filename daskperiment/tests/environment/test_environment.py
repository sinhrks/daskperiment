import pytest

import subprocess
import sys

import daskperiment
import daskperiment.testing
from daskperiment.environment.environment import Environment


class TestEnvironment(object):

    def test_pip_packages(self):
        e = Environment('local')
        res = e.get_python_packages()
        assert any(r.startswith('pandas==') for r in res.splitlines())

    def test_environment(self):
        e = Environment('local')
        res = e.get_environment()
        print(res)

        lines = res.splitlines()
        assert len(lines) == 10

        assert lines[0].startswith('Platform Information:')
        assert lines[1].startswith('Device CPU Count:')
        assert lines[2].startswith('Python Implementation:')
        assert lines[3].startswith('Python Version:')
        assert lines[4].startswith('Python Shell Mode:')
        assert lines[5].startswith('Python venv:')
        assert lines[6].startswith('Daskperiment Version:')
        assert lines[7].startswith('Git Repository:')
        assert lines[8].startswith('Git Active Branch:')
        assert lines[9].startswith('Git HEAD Commit:')


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
        script = ('from daskperiment.environment.environment '
                  'import Environment;'
                  'e = Environment("local");'
                  'print(e.get_python_mode())')

        p = subprocess.Popen([sys.executable, '-c', script],
                             stdout=subprocess.PIPE)
        stdout, stderr = p.communicate()
        assert p.returncode == 0
        assert stdout == b'Interactive Terminal\n'
