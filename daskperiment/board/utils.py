import itertools

import pandas.api.types as types

from bokeh.palettes import all_palettes
from bokeh.models.widgets import TableColumn
from bokeh.models.widgets.tables import DateFormatter


def get_colors(palette, n):
    """
    Return list of colors which length is n
    """
    palletes = all_palettes[palette]

    if n > max(palletes.keys()):
        p = palletes[max(palletes.keys())]
        return [c for _, c in zip(range(n), itertools.cycle(p))]
    else:
        length = n
        while True:
            try:
                return palletes[n][:length]
            except KeyError:
                n = n + 1


def convert_columns(df):
    """
    Convert pandas columns to TableColumn
    """
    def _conv(name, col):
        return TableColumn(field=str(name), title=str(name),
                           formatter=get_formatter(col.dtype))

    return [_conv(name, col) for name, col in df.iteritems()]


def get_formatter(dtype):
    if types.is_datetime64_any_dtype(dtype):
        return DateFormatter(format="%Y-%m-%d %H:%M:%S.%N")
    elif types.is_bool_dtype(dtype):
        return None
        # return BooleanFormatter()
    else:
        return None
