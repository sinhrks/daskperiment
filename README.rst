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

A lightweight tool to perform reproducible data analytics experiments using Dask.

**The package is EXTREMELY unstable.**

Benefits
~~~~~~~~

* Tracking experiment result and its condition (environment, hyper-parameters...).
* User-intuitive. Minimizing modifications of existing codes.
* Parallel execution.

Future Scope
~~~~~~~~~~~~

* Auto saving and loading previous experiment result
* Reproducibility check (function purity check)
* Code version control
* Sharing experiments
* More efficient execution (omit execution if depending parameters are the same)
* Distributed execution
