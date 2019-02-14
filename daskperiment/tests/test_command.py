import pytest

import subprocess
import sys

import pandas as pd
import pandas.testing as tm

import daskperiment
import daskperiment.testing


class TestCommand(object):

    def test_simple_experiment_no_params(self):
        file = 'scripts/simple_experiment.py'

        p = subprocess.Popen([sys.executable, file], stdout=subprocess.PIPE)
        stdout, stderr = p.communicate()
        assert p.returncode == 1

        # cleanup
        e = daskperiment.Experiment('simple_experiment_pj')
        e._delete_cache()

    @pytest.mark.skipif(daskperiment.testing.IS_TRAVIS,
                        reason='skip on Travis CI')
    def test_simple_experiment(self):
        e = daskperiment.Experiment('simple_experiment_pj')
        assert e.trial_id == 0

        file = 'scripts/simple_experiment.py'

        p = subprocess.Popen([sys.executable, file, 'a=1', 'b=2'],
                             stdout=subprocess.PIPE)
        stdout, stderr = p.communicate()
        assert p.returncode == 0

        e = daskperiment.Experiment('simple_experiment_pj')
        assert e.trial_id == 1

        hist = e.get_history()
        exp = pd.DataFrame({'a': [1], 'b': [2], 'Result': [4]},
                           index=pd.Index([1], name='Trial ID'))
        tm.assert_frame_equal(exp[['a', 'b', 'Result']], exp)

        p = subprocess.Popen([sys.executable, file, 'a=3', 'b=5'],
                             stdout=subprocess.PIPE)
        stdout, stderr = p.communicate()
        assert p.returncode == 0

        e = daskperiment.Experiment('simple_experiment_pj')
        hist = e.get_history()
        exp = pd.DataFrame({'a': [1, 3], 'b': [2, 5], 'Result': [4, 9]},
                           index=pd.Index([1, 2], name='Trial ID'))
        tm.assert_frame_equal(hist[['a', 'b', 'Result']], exp)

        # cleanup
        e = daskperiment.Experiment('simple_experiment_pj')
        e._delete_cache()

    @pytest.mark.skipif(daskperiment.testing.IS_TRAVIS,
                        reason='skip on Travis CI')
    def test_random_experiment_no_params(self):
        file = 'scripts/random_experiment.py'

        p = subprocess.Popen([sys.executable, file], stdout=subprocess.PIPE)
        stdout, stderr = p.communicate()
        assert p.returncode == 0

        # provide seed
        p = subprocess.Popen([sys.executable, file, '--seed', '1'],
                             stdout=subprocess.PIPE)
        stdout, stderr = p.communicate()
        assert p.returncode == 0

        # cleanup
        e = daskperiment.Experiment('random_experiment_pj')
        h = e.get_history()
        print(h)
        assert h.loc[1, 'Result'] != 0.5513862488149752
        assert h.loc[2, 'Result'] == 0.5513862488149752

        e._delete_cache()
