import pathlib

from bokeh.models.layouts import Column

import daskperiment
from daskperiment.board.board import DaskperimentBoard, get_resources


class TestBoard(object):

    def test_build_layout(self):
        ex = daskperiment.Experiment('board')

        # empty experiment
        b = DaskperimentBoard(ex)
        app = b.build_layout()
        assert isinstance(app, Column), type(app)

        a = ex.parameter('a')

        @ex.result
        def inc(a):
            return a + 1

        res = inc(a)
        ex.set_parameters(a=1)
        assert res.compute() == 2

        b = DaskperimentBoard(ex)
        app = b.build_layout()
        assert isinstance(app, Column), type(app)

        @ex.result
        def inc(a):
            ex.save_metric('dummy', epoch=1, value=1)
            ex.save_metric('dummy2', epoch=1, value=1)
            return a + 1

        res = inc(a)
        ex.set_parameters(a=2)
        assert res.compute() == 3

        b = DaskperimentBoard(ex)
        app = b.build_layout()
        assert isinstance(app, Column), type(app)

        ex._delete_cache()

    def test_resources(self):
        t = get_resources('templates')
        assert pathlib.Path(t).is_dir()

        s = get_resources('statics')
        assert pathlib.Path(s).is_dir()
