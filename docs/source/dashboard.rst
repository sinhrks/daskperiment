Dashboard
=========

`daskperiment` supports a web dashboard to check experiment histories.

Launch from script
------------------

To launch the dashboard from script, use `Experiment.start_dashboard`.
It should be non-blocking if it is called from interactive
shell like Jupyter, and be blocking if it is executed as a file.


.. code-block:: python

   >>> ex = daskperiment.Experiment('your_experiment_id')
   >>> ex.start_dashboard()


Launch from terminal
--------------------

To launch from the terminal, use `daskperimentboard` command providing your
experiment id.

.. code-block:: sh

   daskperimentboard your_experiment_id


Access to the dashboard
-----------------------

After launching the dashboard, open
`http://localhost:5000/ <http://localhost:5000/>`_ .
