class ParameterUndeclaredError(ValueError):
    """
    Parameter is not declared in the experiment space
    """
    def __init__(self, parameter_name):
        msg = ('Parameter is not declared. '
               'Use Experiment.parameter to declare: {}')
        super().__init__(msg.format(parameter_name))


class ParameterUndefinedError(ValueError):
    """
    Parameter is declared, but not initialized (has no value)
    """
    def __init__(self, parameter_name):
        msg = ('Parameters are not defined. '
               'Use Experiment.set_parameters to initialize: {}')
        super().__init__(msg.format(parameter_name))


class TrialIDNotFoundError(ValueError):
    """
    Trial ID is not found
    """
    def __init__(self, msg):
        if isinstance(msg, int):
            msg = 'Unable to find trial id: {}'.format(msg)
        super().__init__(msg)


class LockedTrialError(ValueError):
    """
    (Current) Trial ID is referred during trial
    """
    def __init__(self, msg):
        if msg is None:
            msg = ('Unable to use TrialManager.trial_id during trial. '
                   'Use .current_trial_id for safety.')
        super().__init__(msg)
