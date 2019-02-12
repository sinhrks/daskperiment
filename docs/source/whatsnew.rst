What's new
==========

v0.3.0
------

Enhancement
^^^^^^^^^^^

* Function purity check
* Random seed handling
* Parameter now supports default value
* (Experimental) Minimal dashboard


Bug fix
^^^^^^^

* `Experiment.get_history` with no parameters results in empty `DataFrame`.

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
