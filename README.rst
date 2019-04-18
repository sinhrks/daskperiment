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

- Compatibility with standard Python/Jupyter environment (and optionally with standard KVS).

  - No need to set up server applications
  - No need to registrate on any cloud services
  - Run on standard / customized Python shells

- Intuitive user interface

  - Few modifications on existing codes are needed
  - Trial histories are logged automatically (no need to write additional codes for logging)
  - `Dask` compatible API
  - Easily accessible experiments history (with `pandas` basic operations)
  - Less managiment works on Git (no need to make branch per trials)
  - (Experimental) Web dashboard to manage trial history

- Traceability of experiment related information

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
  - MongoDB backend

Future Scope
~~~~~~~~~~~~

- More efficient execution.

  - Omit execution if depending parameters are the same
  - Distributed execution
