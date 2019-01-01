import datetime
import json

import pandas as pd


def dumper(obj):
    if isinstance(obj, (pd.Timestamp, datetime.datetime)):
        return obj.isoformat()
    elif isinstance(obj, pd.Timedelta):
        return obj.isoformat()
    elif isinstance(obj, datetime.timedelta):
        return pd.Timedelta(obj).isoformat()
    return obj


def loader(obj):
    if isinstance(obj, list):
        return [loader(o) for o in obj]
    elif isinstance(obj, dict):
        return {k: loader(v) for k, v in obj.items()}
    elif isinstance(obj, str):
        try:
            # TODO: parse only iso format
            return pd.to_datetime(obj, errors='raise')
        except Exception:
            pass
        try:
            # TODO: parse only iso format
            return pd.to_timedelta(obj, errors='raise')
        except Exception:
            pass
    return obj


def dumps(obj):
    return json.dumps(obj, default=dumper)


def loads(obj):
    return json.loads(obj, object_hook=loader)
