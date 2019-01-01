import os


IS_TRAVIS = "TRAVIS" in os.environ and os.environ["TRAVIS"] == "true"


class RedisCleanupMixin(object):

    def setup_class(cls):
        from daskperiment.backend import RedisBackend
        RedisBackend('remove_all', cls.backend)._delete_cache()

    def teardown_class(cls):
        from daskperiment.backend import RedisBackend
        RedisBackend('remove_all', cls.backend)._delete_cache()
