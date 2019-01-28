class ParameterUndeclaredError(ValueError):
    """
    Parameter is not declared in the experiment space
    """
    pass


class ParameterUndefinedError(ValueError):
    """
    Parameter is declared, but not initialized (has no value)
    """
    pass


class TrialIDNotFoundError(ValueError):
    """
    Trial ID is not found
    """
    def __init__(self, msg):
        if isinstance(msg, int):
            msg = 'Unable to find trial id: {}'.format(msg)

        super().__init__(msg)
