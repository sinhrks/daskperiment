daskperiment
============

.. image:: https://img.shields.io/pypi/v/daskperiment.svg
    :target: https://pypi.python.org/pypi/daskperiment/
.. image:: https://readthedocs.org/projects/daskperiment/badge/?version=latest
    :target: http://daskperiment.readthedocs.org/en/latest/
    :alt: Latest Docs
.. image:: https://travis-ci.org/sinhrks/daskperiment.svg?branch=master
    :target: https://travis-ci.org/sinhrks/daskperiment
.. image:: https://coveralls.io/repos/sinhrks/daskperiment/badge.svg?branch=master&service=github
    :target: https://coveralls.io/github/sinhrks/daskperiment?branch=master

Overview
~~~~~~~~

A lightweight tool to perform reproducible machine learning experiment using Dask.

**The package is EXTREMELY unstable.**

Benefits
~~~~~~~~

* User-intuitive.
  * Minimizing modifications of existing codes.
  * Performing experiments using `Dask` compatible API.
  * Easily handle experiments history (with `pandas` basic operations).
  * Requires less work to manage with Git (no need to make branch per trials).
* Tracking experiment result and its (hyper) parameters.
* Tracking environment.
  * OS Info
  * Python version
  * Installed package and its version
* Tracking code context.
* Auto saving and loading previous experiment history.
* Parallel execution of experiment steps.

Future Scope
~~~~~~~~~~~~

* Web Dashboard
* Reproducibility check (function purity check).
* Sharing experiments.
* More efficient execution.
  * Omit execution if depending parameters are the same
  * Distributed execution
