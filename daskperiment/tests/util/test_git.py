import os

import daskperiment
import daskperiment.testing
from daskperiment.util.git import maybe_git_repo


class TestGit(object):

    def test_maybe_git_repo(self):
        res = maybe_git_repo('.')
        assert res.working_dir == os.getcwd()

        if not daskperiment.testing.IS_TRAVIS:
            assert isinstance(res.active_branch.name, str)

        res = maybe_git_repo('daskperiment/tests')
        assert res.working_dir == os.getcwd()

        if not daskperiment.testing.IS_TRAVIS:
            assert isinstance(res.active_branch.name, str)

        res = maybe_git_repo('..')
        assert res is None
