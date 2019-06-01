import pytest

import daskperiment
from daskperiment.environment.git import GitEnvironment


class TestGitEnvironment(object):

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
               'Git HEAD Commit': env.commit,
               'Git Dirty Flag': env.is_dirty}
        assert env.__json__() == exp

    @pytest.mark.skipif(not daskperiment.testing.IS_TRAVIS,
                        reason='run only on Travis CI')
    def test_git_detached(self):
        env = GitEnvironment()
        assert env.branch == 'DETACHED'

    def test_git_roundtrip(self):
        env = GitEnvironment()
        res = env.loads(env.dumps())
        assert env is not res
        assert env == res

    def test_difference(self):
        env1 = GitEnvironment()
        env2 = GitEnvironment()

        env1.repository = 'dummy1'
        env2.repository = 'dummy2'

        res = env2.difference_from(env1)
        exp = ['@@ -2 +2 @@\n',
               '-Git Repository: dummy1',
               '+Git Repository: dummy2']
        assert res == exp

    def test_git_output(self):
        env = GitEnvironment()
        exp = ['Git Repository: {}'.format(env.repository),
               'Git Active Branch: {}'.format(env.branch),
               'Git HEAD Commit: {}'.format(env.commit)]
        assert env.output_init() == exp

    def test_git_output_dirty(self):
        env = GitEnvironment()
        env.is_dirty = True
        exp = ['Git Repository: {}'.format(env.repository),
               'Git Active Branch: {}'.format(env.branch),
               'Git HEAD Commit: {} (DIRTY)'.format(env.commit)]
        assert env.output_init() == exp
