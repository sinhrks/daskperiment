What's new
==========

v0.2.0
------

Enhancement
^^^^^^^^^^^

* Redis backend support

v0.1.1
------

Bug fix
^^^^^^^

* `str` input for experiment function may be incorrectly regarded as a parameter if the same parameter exists.
* Experiment.get_histoy raises `TypeError` in `pandas` 0.22 or earliner
* Experiment may raise `AttributeError` depending on `pip` version

v0.1.0
------

* Initial release
