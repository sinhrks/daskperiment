daskperiment
============

.. image:: https://img.shields.io/pypi/v/daskperiment.svg
  :target: https://pypi.python.org/pypi/daskperiment/
.. image:: https://readthedocs.org/projects/daskperiment/badge/?version=latest
  :target: http://daskperiment.readthedocs.org/en/latest/
  :alt: Latest Docs
.. image:: https://travis-ci.org/sinhrks/daskperiment.svg?branch=master
  :target: https://travis-ci.org/sinhrks/daskperiment
.. image:: https://codecov.io/gh/sinhrks/daskperiment/branch/master/graph/badge.svg
  :target: https://codecov.io/gh/sinhrks/daskperiment

Overview
~~~~~~~~

`daskperiment` is a tool to perform reproducible machine learning experiment.
It allows users to define and manage the history of trials
(given parameters, results and execution environment).

The package is built on `Dask`, a package for parallel computing with task
scheduling. Each experiment trial is internally expressed as `Dask` computation
graph, and can be executed in parallel.

Benefits
~~~~~~~~

- Usable in standard Python/Jupyter environment (and optionally with standard KVS).

  - No need to setting up server applications.
  - No registration to cloud services.
  - Not to be constrained by slightly customized Python shells.

- User-intuitive.

  - Minimizing modifications of existing codes.
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

Future Scope
~~~~~~~~~~~~

- More efficient execution.

  - Omit execution if depending parameters are the same
  - Distributed execution
