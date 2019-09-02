from daskperiment.util.log import get_logger

logger = get_logger(__name__)


def maybe_git_repo(path):
    try:
        import git
    except ImportError:
        msg = ('To collect git related information, '
               'gitpython must be installed')
        logger.error(msg)
        return None

    try:
        repo = git.Repo(path, search_parent_directories=True)
        return repo
    except git.InvalidGitRepositoryError:
        return None
