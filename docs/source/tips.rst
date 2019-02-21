Monitor trial related information
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
