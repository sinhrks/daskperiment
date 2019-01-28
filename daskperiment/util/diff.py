import difflib


def unified_diff(a, b, n=3):
    if isinstance(a, str):
        a = a.splitlines()
    if isinstance(b, str):
        b = b.splitlines()
    g = difflib.unified_diff(a, b, n=n)
    # skip header
    try:
        next(g)
        next(g)
        return g
    except StopIteration:
        # return empty string
        return [""]
