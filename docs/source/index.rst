Welcome to daskperiment's documentation!
========================================

`daskperiment` is a tool to perform reproducible machine learning experiment.
It allows users to define and manage the history of trials
(given parameters, results and execution environment).

The package is built on `Dask`, a package for parallel computing with task
scheduling. Each experiment trial is internally expressed as `Dask` computation
graph, and can be executed in parallel.

It can be used in both Jupyter and command line (and also in standard Python interpreter). The benefits of daskperiemnt are:

- Usable in standard Python /Jupyter environment (and optionally KVS).

  - No need to:

    - Setting up server applications.
    - Register to cloud services.
    - Be constrained by slightly customized Python shells.

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


Contents:

.. toctree::
   :maxdepth: 2

   whatsnew
   quickstart
   commandline
   backend
