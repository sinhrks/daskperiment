What's new
==========

v0.x.x
------

Enhancement
^^^^^^^^^^^

Bug fix
^^^^^^^

* Trial result may be incorrect if it is ran from multiple threads

v0.4.0
------

Enhancement
^^^^^^^^^^^

* Added `verbose` option to `Experiment.get_history` (default `False`)
* Environment now collects following info:

  * Detailed CPU info with `py-cpuinfo`
  * `conda info`
  * `numpy.show_config()`
  * `scipy.show_config()`
  * `pandas.show_versions()`

* Dashboard now supports to show summary, code and environment info.

Bug fix
^^^^^^^

* Log output of "number of installed python packages" is incorrect
* Dashboard can't switch display metric name

v0.3.0
------

Enhancement
^^^^^^^^^^^

* Function purity check
* Random seed handling
* Parameter now supports default value
* Capture Git info
* (Experimental) Minimal dashboard

Bug fix
^^^^^^^

* `Experiment.get_history` with no parameters results in empty `DataFrame`.
* Unable to change log level and its handler one time.

v0.2.0
------

Enhancement
^^^^^^^^^^^

* Redis backend support
* "Result Type" column is added to a `DataFrame` which `Experiment.get_history` returns
  (as `pandas` may change column dtype)

v0.1.1
------

Bug fix
^^^^^^^

* `str` input for experiment function may be incorrectly regarded as a parameter if the same parameter exists.
* Experiment.get_histoy raises `TypeError` in `pandas` 0.22 or earlier
* Experiment may raise `AttributeError` depending on `pip` version

v0.1.0
------

* Initial release
