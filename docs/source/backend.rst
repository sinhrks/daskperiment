Backend
=======

`daskperiment` uses `Backend` classes to define how and where experiment results are saved. Currently, following backends are supported.

* `LocalBackend`: Information is stored in local files. This is for personal
  usage with single PC. This backend doesn't intends to share information with
  others and move file(s) to another PC.
* `RedisBackend`: Information is stored in redis. If you setup redis-server,
  information can be shared in small team and between PCs.

You can specify required `Backend` via `backend` keyword in `Experiment` instanciation.

LocalBackend
------------

`LocalBackend` saves information as local files. When you create `Experiment` instance without `backend` argument, the `Experiment` uses `LocalBackend` to save its information.

.. note::

   Following examples omit unrelated logs.

.. code-block:: python

   >>> import daskperiment
   >>> daskperiment.Experiment('local_default_backend')
   2019-02-03 XX:XX:XX,XXX [daskperiment.io.pickle] [INFO] Creating new cache directory: /Users/sinhrks/Git/daskperiment/daskperiment_cache/local_default_backend
   2019-02-03 XX:XX:XX,XXX [daskperiment.core.experiment] [INFO] Initialized new experiment: Experiment(id: local_default_backend, trial_id: 0, backend: LocalBackend('daskperiment_cache/local_default_backend'))
   ...
   Experiment(id: local_default_backend, trial_id: 0, backend: LocalBackend('daskperiment_cache/local_default_backend'))

To change the directory location, passing `pathlib.Path` instance as `backend` makes `LocalBackend` with custom location.

.. code-block:: python

   >>> import pathlib
   >>> daskperiment.Experiment('local_custom_backend', backend=pathlib.Path('my_dir'))
   2019-02-03 XX:XX:XX,XXX [daskperiment.io.pickle] [INFO] Creating new cache directory: /Users/sinhrks/Git/daskperiment/my_dir
   2019-02-03 XX:XX:XX,XXX [daskperiment.core.experiment] [INFO] Initialized new experiment: Experiment(id: local_custom_backend, trial_id: 0, backend: LocalBackend('my_dir'))
   ...
   Experiment(id: local_custom_backend, trial_id: 0, backend: LocalBackend('my_dir'))


The following table shows information and its saved location under cache directory specified in `LocalBackend`.

================================== ====== ===================
Information                        Format Path
================================== ====== ===================
Experiment Status (internal state) Pickle <experiment id>.pkl
Experiment History                 Pickle <experiment id>.pkl
Persisted Results                  Pickle persist/<experiment id>_<function name>_<trial id>.pkl
Metrics                            Pickle <experiment id>.pkl
Code contexts                      Text   code/<experiment id>_<trial id>.py
Device Information                 Text   environmemt/requirements_<experiment id>_<trial id>.txt
Python Package Information         Text   environmemt/device_<experiment id>_<trial id>.txt
================================== ====== ===================


RedisBackend
------------

`RedisBackend` saves information using `Redis`. To use `RedisBackend`, simple way is specifying Redis URI as `backend` argument.

.. code-block:: python

   >>> daskperiment.Experiment('redis_uri_backend', backend='redis://localhost:6379/0')
   2019-02-03 XX:XX:XX,XXX [daskperiment.core.experiment] [INFO] Initialized new experiment: Experiment(id: redis_uri_backend, trial_id: 0, backend: RedisBackend('redis://localhost:6379/0'))
   ...
   Experiment(id: redis_uri_backend, trial_id: 0, backend: RedisBackend('redis://localhost:6379/0'))

Or, you can use `redis.ConnectionPool`.

   >>> import redis
   >>> pool = redis.ConnectionPool.from_uri('redis://localhost:6379/0')
   >>> daskperiment.Experiment('redis_pool_backend', backend=pool)
   2019-02-03 XX:XX:XX,XXX [daskperiment.core.experiment] [INFO] Initialized new experiment: Experiment(id: redis_pool_backend, trial_id: 0, backend: RedisBackend('redis://localhost:6379/0'))
   ...
   Experiment(id: redis_pool_backend, trial_id: 0, backend: RedisBackend('redis://localhost:6379/0'))


The following table shows information and its saved location under Redis database specified in `RedisBackend`.

================================== ====== ===================
Information                        Format Key
================================== ====== ===================
Experiment Status (internal state) Text   <experiment id>:trial_id
Experiment History (parameters)    Pickle <experiment id>:parameter:<trial id>
Experiment History (results)       Pickle <experiment id>:history:<trial id>
Persisted Results                  Pickle <experiment_id>:persist:<function name>:<trial id>
Metrics                            Pickle <experiment id>:metric:<metric name>:<trial id>
Code contexts                      Text   <experiment_id>:code:<trial id>
Device Information                 Text   <experiment_id>:requirements:<trial id>
Python Package Information         Text   <experiment_id>:device:<trial id>
================================== ====== ===================
