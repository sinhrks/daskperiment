Welcome to daskperiment's documentation!
========================================

`daskperiment` is a tool to perform reproducible machine learning experiment.
It allows users to define and manage the history of trials
(given parameters, results and execution environment).

The package is built on `Dask`, a package for parallel computing with task
scheduling. Each experiment trial is internally expressed as `Dask` computation
graph, and can be executed in parallel.

It can be used in both Jupyter and command line (and also in standard Python interpreter). The benefits of daskperiemnt are:

- Usable in standard Python/Jupyter environment (and optionally with standard KVS).

  - No need to setting up server applications.
  - No registration to cloud services.
  - Not to be constrained by slightly customized Python shells.

- User-intuitive.

  - Minimizing modifications of existing codes.
  - Logging automatically (no need to write additional codes for logging)
  - Performing experiments using `Dask` compatible API.
  - Easily handle experiments history (with `pandas` basic operations).
  - Requires less work to manage with Git (no need to make branch per trials).
  - (Experimental) Web dashboard to manage trial history.

- Tracking experiment related information
  - Trial result and its (hyper) parameters.
  - Code context.
  - Environment information.

    - Device information
    - OS information
    - Python version
    - Installed Python packages and its version
    - Git information

- Reproducibility

  - Check function purity (each step should return the same output for the same inputs)
  - Automatic random seeding

- Auto saving and loading previous experiment history.
- Parallel execution of experiment steps.
- Sharing experiments.

  - Redis backend

Contents:

.. toctree::
   :maxdepth: 2

   whatsnew
   quickstart
   dashboard
   commandline
   backend
