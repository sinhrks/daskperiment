import os
import pathlib

from daskperiment.environment.base import _EnvironmentJsonDataClass
from daskperiment.util.git import maybe_git_repo
from daskperiment.util.log import get_logger


logger = get_logger(__name__)


class GitEnvironment(_EnvironmentJsonDataClass):
    """
    Handle Git info

    * Git repo directory
    * Active branch
    """

    key = 'git'

    __slots__ = ('working_dir', 'repository', 'branch',
                 'commit', 'is_dirty')

    _WORKING_DIR = 'Working Directory'
    _REPOSITORY = 'Git Repository'
    _BRANCH = 'Git Active Branch'
    _COMMIT = 'Git HEAD Commit'
    _IS_DIRTY = 'Git Dirty Flag'

    def __init__(self):
        self.working_dir = str(pathlib.Path.cwd())

        repo = maybe_git_repo(os.getcwd())
        if repo is None:
            self.repository = 'Not Git Controlled'
            self.branch = 'Not Git Controlled'
            self.commit = 'Not Git Controlled'
        else:
            self.repository = repo.working_dir
            try:
                self.branch = repo.active_branch.name
            except TypeError:
                # If this symbolic reference is detached,
                # cannot retrieve active_branch
                self.branch = 'DETACHED'
            self.commit = repo.head.commit.hexsha
            self.is_dirty = repo.is_dirty()

        # TODO: get diff from previous commit if dirty
        # repo.head.commit.diff(None)

    def output_init(self):
        res = []
        for key in ('repository', 'branch'):
            disp = getattr(self, '_{}'.format(key.upper()))
            res.append('{}: {}'.format(disp, getattr(self, key)))

        if self.is_dirty:
            res.append('{}: {} (DIRTY)'.format(self._COMMIT, self.commit))
        else:
            res.append('{}: {}'.format(self._COMMIT, self.commit))
        return res
