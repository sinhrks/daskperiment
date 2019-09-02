import pytest

import pandas as pd

from bokeh.palettes import all_palettes
from bokeh.models.widgets.tables import DateFormatter

from daskperiment.board.utils import convert_columns, get_colors


class TestBoardUtils(object):

    def test_convert_columns(self):
        df = pd.DataFrame({0: [1, 2],
                           1: [1.1, 2.2],
                           2: ['a', 'b'],
                           3: [pd.Timestamp.now()] * 2,
                           4: [pd.Timestamp.now(tz='GMT')] * 2,
                           5: [True, False],
                           6: [pd.Timedelta(1), pd.Timedelta(2)]})

        res = convert_columns(df)
        assert res[0].formatter is None
        assert res[1].formatter is None
        assert res[2].formatter is None
        assert isinstance(res[3].formatter, DateFormatter)
        assert isinstance(res[4].formatter, DateFormatter)
        assert res[5].formatter is None
        assert res[6].formatter is None

    @pytest.mark.parametrize('pallete', ['Magma', 'Inferno', 'Plasma',
                                         'Viridis'])
    def test_get_colors(self, pallete):
        for i in [1, 2, 3]:
            res = get_colors(pallete, i)
            assert len(res) == i
            assert res == all_palettes[pallete][3][:i]

        for i in [4, 5, 6, 7, 8, 9, 10, 11]:
            res = get_colors(pallete, i)
            assert len(res) == i
            assert res == all_palettes[pallete][i]

        for i in [20, 30, 50, 100, 200, 256]:
            res = get_colors(pallete, i)
            assert len(res) == i
        assert res == all_palettes[pallete][256][:i]

    @pytest.mark.parametrize('pallete', ['Blues', 'BuGn', 'BuPu', 'GnBu',
                                         'Greens', 'OrRd', 'Oranges',
                                         'Pastel1', 'PuBu', 'PuBuGn', 'PuRd',
                                         'Purples', 'RdPu', 'Reds', 'Set1',
                                         'YlGn', 'YlGnBu', 'YlOrBr', 'YlOrRd'])
    def test_get_color_cycle(self, pallete):
        for i in [1, 2, 3]:
            res = get_colors(pallete, i)
            assert len(res) == i
            assert res == all_palettes[pallete][3][:i]

        for i in [4, 5, 6, 7, 8, 9]:
            res = get_colors(pallete, i)
            assert len(res) == i
            assert res == all_palettes[pallete][i]

        # cycles
        for i in [10, 20, 30, 50, 100]:
            res = get_colors(pallete, i)
            assert len(res) == i
        assert res == (all_palettes[pallete][9] * 20)[:i]

    @pytest.mark.parametrize('pallete', ['Colorblind'])
    def test_get_color_blind(self, pallete):
        for i in [1, 2, 3]:
            res = get_colors(pallete, i)
            assert len(res) == i
            assert res == all_palettes[pallete][3][:i]

        for i in [4, 5, 6, 7, 8]:
            res = get_colors(pallete, i)
            assert len(res) == i
            assert res == all_palettes[pallete][i]

        # cycles
        for i in [10, 20, 30, 50, 100]:
            res = get_colors(pallete, i)
            assert len(res) == i
        assert res == (all_palettes[pallete][8] * 20)[:i]
