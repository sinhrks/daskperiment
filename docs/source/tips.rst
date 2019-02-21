Tips
====

Monitor Trial Related Information
---------------------------------

You may want to log trial related information such as user who performs the trial, etc. The easiest way is including these information in parameters.

.. code-block:: python

   >>> ex.parameter('user_name')
   >>> ex.set_parameters(..., user_name='my_name')


Track Data Version
------------------

Most of experiments relies on external data source such as CSV, relational DB, etc. Sometimes experiment result is unexpectedly changed because of external data changes. In such cases, even though `daskperiment` checks function purity and shows a warning, users may not determine the exact reason.

Splitting data loading function as a separate step is recommended
because if the function shows a warning, it indicates external data changes.

.. code-block:: python

   >>> @ex
   >>> def load_user_data(filename):
   >>>     return pd.read_csv(filename)


Check Trial ID During Execution
-------------------------------

You may want to know the current trial id during the trial.
Use `Experiment.current_trial_id` to check current trial id.

.. code-block:: python

  >>> @ex
  >>> def experiment_step(a, b):
  >>>     print('debug_information', ex.current_trial_id)
  >>>     ...

You cannnot refer to `current_trial_id` outside from the experiment step
because the id is generated when the trial is performed.

.. code-block:: python

  >>> ex.current_trial_id
  daskperiment.core.errors.TrialIDNotFoundError: Current Trial ID only exists during a trial execution

To check the last trial id of the experiment outside from the experiment step,
use `.trial_id` property.

.. code-block:: python

  >>> ex.trial_id
  3

The next trial should be numbered as `.trial_id + 1`, if no other trial is triggered until your execution.
Note that `.trial_id` cannot be referred during a trial execution to avoid confusion between
`.trial_id` and `.current_trial_id`.
