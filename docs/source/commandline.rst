Command Line Interface
======================


`daskperiment` also supports execution from command line.

First, prepare a `Python` script to define experiment. The usage of `Experiment` class is all the same as Jupyter example. `daskperiment` regards a result of a function decorated with `Experiment.result` (`calculate_score` function in below case) as experiment output.

The below is a prepared script named "simple_experiment.py".

.. code-block:: python

   import daskperiment

   ex = daskperiment.Experiment(id='simple_experiment_pj')

   a = ex.parameter('a')
   b = ex.parameter('b')

   @ex
   def prepare_data(a, b):
       return a + b

   @ex.result
   def calculate_score(s):
       return s + 1

   d = prepare_data(a, b)
   calculate_score(d)

You can provide parameter values from command line options using `key=value` format. `daskperinemt` automatically parse parameters and perform computation.

.. code-block:: sh

   python simple_experiment.py a=1 b=2

   ... [INFO] Initialized new experiment: Experiment(id: simple_experiment_pj, trial_id: 0, backend: LocalBackend('daskperiment_cache/simple_experiment_pj'))
   ...
   ... [INFO] Finished Experiment (trial id=1)
   ...

Let's perform another trial using different parameters. daskperiment automatically saves trial history as the same as Jupyter example (see trial id is incremented).

.. code-block:: sh

   python ../scripts/simple_experiment.py a=3 b=2

   ... [INFO] Loading Experiment from file: daskperiment_cache/simple_experiment_pj/simple_experiment_pj.pkl
   ...
   ... [INFO] Finished Experiment (trial id=2)
   ...

To confirm the experiment results, instanciate `Experiment` specifying the same id as the script and use `Experiment.get_history`.

.. code-block:: python

   >>> import daskperiment

   >>> ex = daskperiment.Experiment(id='simple_experiment_pj')
   >>> ex.get_history()
      a  b  Result    Result Type  Success                   Finished  \
   1  1  2       4  <class 'int'>     True 2019-02-03 XX:XX:XX.XXXXXX
   2  3  2       6  <class 'int'>     True 2019-02-03 XX:XX:XX.XXXXXX

     Process Time  Description
   1 00:00:00.009560          NaN
   2 00:00:00.006512          NaN
