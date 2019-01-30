import os


def validate_key(key, keyname='Key'):
    """
    Check input is valid key (Experiment id, metric name...)
    """
    if not isinstance(key, str):
        msg = '{} must be str, given: {}{}'
        raise ValueError(msg.format(keyname, key, type(key)))
    if ':' in key:
        msg = '{} cannot contain colon (:): {}'
        raise ValueError(msg.format(keyname, key))
    return key


def trim_indent(text):
    assert isinstance(text, str)
    endsep = text.endswith(os.linesep)
    texts = text.splitlines()

    if len(texts) == 0:
        return text

    first_line = texts[0]
    indent = len(first_line) - len(first_line.lstrip(' '))
    if indent == 0:
        return text

    def _trim(text, indent):
        if len(text) <= indent:
            return ''
        else:
            return text[indent:]

    texts = [_trim(text, indent) for text in texts]

    if endsep:
        return os.linesep.join(texts) + os.linesep
    else:
        return os.linesep.join(texts)
