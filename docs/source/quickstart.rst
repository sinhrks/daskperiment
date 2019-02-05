Quickstart
==========

`daskperiment` is a tool to perform reproducible machine learning experiment.
It allows users to define and manage the history of trials
(given parameters, results and execution environment).

The package is built on `Dask`, a package for parallel computing with task
scheduling. Each experiment trial is internally expressed as `Dask` computation
graph, and can be executed in parallel.

It can be used in both Jupyter and command line (and also in standard Python interpreter). The benefits of daskperiemnt are:

- User-intuitive.

  - Minimizing modifications of existing codes.
  - Performing experiments using `Dask` compatible API.
  - Easily handle experiments history (with `pandas` basic operations).
  - Requires less work to manage with Git (no need to make branch per trials).

- Tracking experiment result and its (hyper) parameters.
- Tracking environment.

  - OS Info
  - Python version
  - Installed package and its version

- Tracking code context.
- Auto saving and loading previous experiment history.
- Parallel execution of experiment steps.
- Sharing experiments.

  - Redis backend


Minimal Example
---------------

First, create `daskperiment.Experiment` instance. This instance controlls an experiment, a chain of functions to output value and a collection of input variables.

.. note::

   Following examples omit unrelated logs.

.. code-block:: python

   >>> import numpy as np
   >>> import daskperiment

   >>> ex = daskperiment.Experiment(id='quickstart_pj')
   ...
   >>> ex
   Experiment(id: quickstart_pj, trial_id: 0, backend: LocalBackend('daskperiment_cache/quickstart_pj'))


Then, use `Experiment.parameter` method to define parameters (input variables for the experiment). The actual value of each parameter can be changed in every trial.

.. code-block:: python

   >>> a = ex.parameter('a')
   >>> b = ex.parameter('b')
   >>> a
   Parameter(a: Undefined)


Next, you can define each experiment step (function) by decorating with Experiment instance (`@ex`).

Note that the function to output the final result (mostly objective value to be minimized or maximized) must be decorated with `Experiment.result`. The chain of these functions are expressed as `Dask.Delayed` instance.


.. code-block:: python

   >>> @ex
   >>> def prepare_data(a, b):
   >>>     return a + b

   >>> @ex.result
   >>> def calculate_score(s):
   >>>     return 10 / s

   >>> d = prepare_data(a, b)
   >>> s = calculate_score(d)
   >>> s
   Delayed('calculate_score-ebe2d261-8903-45e1-b224-72b4c886e4c5')


Thus, you can visualize computation graph via `.visualize` method.


.. code-block:: python

   >>> s.visualize()


Use `Experiment.set_parameters` method to set parameters for a trial. After setting parameters, `Parameter` variable and experiment result will be computable.

Parameters are recommended to be a scalar (or lightweight value) because these are stored as history (for example, passing filename as a parameter is preffered rather than passing `DataFrame`).


.. code-block:: python

   >>> ex.set_parameters(a=1, b=2)
   ...


.. code-block:: python

   >>> s.compute()
   ... [INFO] Started Experiment (trial id=1)
   ...
   ... [INFO] Finished Experiment (trial id=1)
   ...
   3.3333333333333335


You can update any parameters for next trial. Every trials can be distinguished by trial id.


.. code-block:: python

   >>> ex.set_parameters(b=3)
   >>> s.compute()
   ...
   ... [INFO] Started Experiment (trial id=2)
   ...
   ... [INFO] Finished Experiment (trial id=2)
   ...
   2.5


After some trials, you can retrieve parameter values specifying trial id.


.. code-block:: python

   >>> ex.get_parameters(trial_id=1)
   {'a': 1, 'b': 2}

   >>> ex.get_parameters(trial_id=2)
   {'a': 1, 'b': 3}


`Experiment.get_history` will return a `DataFrame` which stores a history of trial parameters and its results. You can select desirable trial using `pandas` basic operation.


.. code-block:: python

   >>> ex.get_history()
             a  b  Result    Result Type  Success                   Finished  \
   Trial ID
   1         1  2       4  <class 'int'>     True 2019-02-03 XX:XX:XX.XXXXXX
   2         3  2       6  <class 'int'>     True 2019-02-03 XX:XX:XX.XXXXXX

               Process Time  Description
   Trial ID
   1        00:00:00.008514          NaN
   2        00:00:00.005247          NaN


When any error occurs during the trial, Experiment instance stores the log as failed trial. The "Description" column contains the error detail.

.. code-block:: python

   >>> ex.set_parameters(a=1, b=-1)
   >>> s.compute()
   ...
   ZeroDivisionError: division by zero

   >>> ex.get_history()
      a  b    Result      Result Type  Success                   Finished  \
   1  1  2  3.333333  <class 'float'>     True 2019-02-03 XX:XX:XX.XXXXXX
   2  1  3  2.500000  <class 'float'>     True 2019-02-03 XX:XX:XX.XXXXXX
   3  1 -1       NaN             None    False 2019-02-03 XX:XX:XX.XXXXXX

        Process Time                          Description
   1 00:00:00.014183                                  NaN
   2 00:00:00.012354                                  NaN
   3 00:00:00.015954  ZeroDivisionError(division by zero)


Handling Intermediate Result
----------------------------

Next example shows how to retrieve an intermediate result of the chain.

The only difference is using `Experiment.persist` decorator. It makes `Experiment` instance to keep the decorated function's intermediate result. After definition, rebuilt the same workflow using the persisted function.

Note that an intermediate result is saved as a pickle file named with its function name, function name must be unique in the experiment.

.. code-block:: python

   >>> @ex.persist
   >>> def prepare_data(a, b):
   >>>     return a + b

   >>> d = prepare_data(a, b)
   >>> s = calculate_score(d)
   ... [WARNING] Code context has been changed: prepare_data
   ... [WARNING] @@ -1,3 +1,3 @@
   ... [WARNING] -@ex
   ... [WARNING] +@ex.persist
   ... [WARNING]  def prepare_data(a, b):
   ... [WARNING]      return a + b

   ...

.. note::

   If you execute the code above, `daskperiment` outputs some "WARNING" indicating code contexts has been changed. It's because `daskperiment` automatically tracks code context to guarantee reproducibility.


Let's perform some trials.


.. code-block:: python

   >>> ex.set_parameters(a=1, b=2)
   >>> s.compute()
   ...
   ... [INFO] Finished Experiment (trial id=4)
   ...
   3.3333333333333335

   >>> ex.set_parameters(a=3, b=2)
   >>> s.compute()
   ...
   ... [INFO] Finished Experiment (trial id=5)
   ...
   2.0


You can retrieve intermediate results via Experiment.get_persisted method by specifying function name and trial id.


.. code-block:: python

   >>> ex.get_persisted('prepare_data', trial_id=4)
   ...
   3

   >>> ex.get_persisted('prepare_data', trial_id=5)
   ...
   5


Monitoring Metrics
------------------

You may need to monitor transition of some metrics during each trial. In each experiment function, you can call `Experiment.save_metric` to save metric with its key (name) and epoch.


.. code-block:: python

   >>> @ex.result
   >>> def calculate_score(s):
   >>>     for i in range(100):
   >>>         ex.save_metric('dummy_score', epoch=i, value=100 - np.random.random() * i)
   >>>     return 10 / s

   >>> d = prepare_data(a, b)
   >>> s = calculate_score(d)
   ...

   >>> ex.set_parameters(a=1, b=2)
   >>> s.compute()
   ...
   ... [INFO] Finished Experiment (trial id=6)
   ...
   3.3333333333333335


After a trial, you can load saved metric using `Experiment.load_metric` specifying its name and trial_id. As it is returned as `DataFrame`, you can easily investigate it.

.. code-block:: python

   >>> dummy_score = ex.load_metric('dummy_score', trial_id=6)
   >>> dummy_score.head()
   Trial ID           6
   Epoch
   0         100.000000
   1          99.925724
   2          99.616405
   3          98.527259
   4          97.086730

Perform another trial.

.. code-block:: python

   >>> ex.set_parameters(a=3, b=4)
   >>> s.compute()
   ...
   ... [INFO] Finished Experiment (trial id=7)
   ...
   1.4285714285714286


To compare metrics between trials, pass multiple trial ids to `Experiment.load_metric`.

.. code-block:: python

   >>> ex.load_metric('dummy_score', trial_id=[6, 7]).head()
   Trial ID           6           7
   Epoch
   0         100.000000  100.000000
   1          99.925724   99.497605
   2          99.616405   99.459706
   3          98.527259   98.027079
   4          97.086730   99.517617

Check Code Context
------------------

During the trials, `daskperiment` tracks code contexts decorated with `Experiment` decorators.

To check the tracked code contexts, use `Experiment.get_code` specifying trial id (shows current code if trial id is not provided).


.. code-block:: python

   >>> ex.get_code()
   @ex.persist
   def prepare_data(a, b):
       return a + b


   @ex.result
   def calculate_score(s):
       for i in range(100):
           ex.save_metric('dummy_score', epoch=i, value=100 - np.random.random() * i)

       return 10 / s

   >>> ex.get_code(trial_id=1)
   @ex
   def prepare_data(a, b):
       return a + b


   @ex.result
   def calculate_score(s):
       return 10 / s

Each code context is also saved as a text file per trial id. Thus, these are easily handled by diff tools and Git.


Save Experiment Result
----------------------


`daskperiment` automatically saves its internal state when the experiment result is computed (when `.compute` is called). Also, `Experiment` instance automatically recover previous state when it is instanciated.

Following example instanciates `Experiment` instance using the same id as above. Thus, the created `Experiment` automatically recovers its state.

.. code-block:: python

   >>> ex_new = daskperiment.Experiment(id='quickstart_pj')

Calling `.get_history` returns information of previous trials.

.. code-block:: python

   >>> ex_new.get_history()
   ...


Also, `Experiment` instance automatically detects the environment change from its previous trial. Following is a sample log when package update is detected (`pandas` 0.23.4 -> 0.24.0).


.. code-block:: python

   ... [INFO] Loaded Experiment(id: quickstart_pj, trial_id: 14) from path=daskperiment_cache/quickstart_pj/quickstart_pj.pkl
   ... [WARNING] Installed Python packages have been changed
   ... [WARNING] @@ -142 +142 @@
   ... [WARNING] -pandas 0.23.4 (/Users/sinhrks/anaconda/lib/python3.6/site-packages)
   ... [WARNING] +pandas 0.24.0 (/Users/sinhrks/anaconda/lib/python3.6/site-packages)
