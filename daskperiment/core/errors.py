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
