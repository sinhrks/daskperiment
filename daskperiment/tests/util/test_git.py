import pytest

import os

import daskperiment
import daskperiment.testing
from daskperiment.util.git import maybe_git_repo


class TestGit(object):

    @pytest.mark.skipif(daskperiment.testing.IS_TRAVIS,
                        reason='skip on Travis CI')
    def test_maybe_git_repo(self):
        res = maybe_git_repo('.')
        assert res.working_dir == os.getcwd()
        assert isinstance(res.active_branch.name, str)

        res = maybe_git_repo('daskperiment/tests')
        assert res.working_dir == os.getcwd()
        assert isinstance(res.active_branch.name, str)

        res = maybe_git_repo('..')
        assert res is None
