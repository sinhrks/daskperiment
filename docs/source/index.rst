Welcome to daskperiment's documentation!
========================================

`daskperiment` is a tool to perform reproducible machine learning experiment.
It enables users to define and manage the history of trials
(given parameters, results and execution environment).

This package is built on `Dask`, a package for parallel computing with task
scheduling. Each experiment trial is internally expressed as `Dask` computation
graph, and can be executed in parallel.

It can be used both on Jupyter and command line (and also on standard Python interpreter). The benefits of daskperiemnt are:

- Compatibility with standard Python/Jupyter environment (and optionally with standard KVS).

  - No need to set up server applications
  - No need to registrate on any cloud services
  - Run on standard / customized Python shells

-Intuitive user interface

  - Few modifications on existing codes are needed
  - Trial histories are logged automatically (no need to write additional codes for logging)
  - `Dask` compatible API
  - Easily accessible experiments history (with `pandas` basic operations)
  - Less managiment works on Git (no need to make branch per trials)
  - (Experimental) Web dashboard to manage trial history

-Traceability of experiment related information

  - Trial result and its (hyper) parameters.
  - Code contexts
  - Environment information

    - Device information
    - OS information
    - Python version
    - Installed Python packages and its version
    - Git information

- Reproducibility

  - Check function purity (each step should return the same output for the same inputs)
  - Automatic random seeding

- Auto saving and loading of previous experiment history
- Parallel execution of experiment steps
- Experiment sharing

  - Redis backend

Contents:

.. toctree::
   :maxdepth: 2

   whatsnew
   quickstart
   dashboard
   commandline
   tips
   backend
