import pytest

import subprocess
import sys

import daskperiment
import daskperiment.testing
from daskperiment.core.environment import Environment


class TestEnvironment(object):

    def test_python_mode_test(self):
        e = Environment()
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
                  'e = Environment();'
                  'print(e.get_python_mode())')

        p = subprocess.Popen([sys.executable, '-c', script],
                             stdout=subprocess.PIPE)
        stdout, stderr = p.communicate()
        assert p.returncode == 0
        assert stdout == b'Interactive Terminal\n'
