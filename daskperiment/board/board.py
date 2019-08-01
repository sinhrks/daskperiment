import pathlib

import numpy as np
import bokeh.layouts as layouts
from bokeh.models.widgets import Div, Tabs

import daskperiment
from daskperiment.board.component import (SummaryPanel,
                                          MetricPanel,
                                          CodePanel,
                                          EnvironmentPanel)
from daskperiment.board.utils import convert_columns


# TODO: get screeninfo
WIDTH = 1200
HEIGHT = 650


def get_resources(name):
    return str(pathlib.Path(__file__).parent / name)


class DaskperimentBoard(object):

    _STARTED = False

    def __init__(self, experiment, palette='Viridis',
                 width=WIDTH, height=HEIGHT):
        self.experiment = experiment
        self.palette = palette

        self.width = width
        self.height = height

    def build_layout(self):
        from bokeh.models import ColumnDataSource
        from bokeh.models.widgets import DataTable

        history = self.experiment.get_history(verbose=True)
        history = history.reset_index()
        self.history = history

        source = ColumnDataSource(history)

        columns = convert_columns(history)
        dt = DataTable(source=source, columns=columns,
                       width=WIDTH, height=int(HEIGHT * 0.6))

        source.selected.on_change('indices', self.callback_datatable_select)
        self.source = source

        # trial IDs selected on DataTable
        self.trial_ids = []

        tabs = self.build_tabs()
        title = Div(text='<h1>Trial Results</h1>')
        layout = layouts.layout([[title], [dt], [tabs]],
                                sizing_mode='scale_width')

        self.layout = layout
        return self.layout

    def make_document(self, doc):
        from jinja2 import Environment, FileSystemLoader

        TEMPLATE = get_resources('templates')
        env = Environment(loader=FileSystemLoader(TEMPLATE))

        layout = self.build_layout()
        doc.template = env.get_template('index.html')
        doc.add_root(layout)
        doc.title = 'daskperiment: {}'.format(self.experiment.id)
        return doc

    def build_tabs(self):
        self.summary_tab = SummaryPanel(self)
        self.metric_tab = MetricPanel(self)
        self.code_tab = CodePanel(self)
        self.environment_tab = EnvironmentPanel(self)
        # TODO: Log output

        return Tabs(tabs=[self.summary_tab.build(),
                          self.metric_tab.build(),
                          self.code_tab.build(),
                          self.environment_tab.build()],
                    sizing_mode='scale_width')

    def callback_datatable_select(self, attr, old, selected):
        """
        Callback to update metric plot based on DataTable selection
        """
        # mapping selected indices to trial ids
        self.trial_ids = [int(self.history['Trial ID'].iloc[i])
                          for i in selected]
        self.metric_tab.update_content()
        self.code_tab.update_content()
        self.environment_tab.update_content()


def maybe_start_dashboard(experiment, port=5000):
    if DaskperimentBoard._STARTED:
        # do not run duplicatedly
        # shoud find better way...
        return

    from bokeh.application import Application
    from bokeh.application.handlers.function import FunctionHandler
    from bokeh.server.server import Server
    from tornado.web import StaticFileHandler

    h = DaskperimentBoard(experiment)

    apps = {'/': Application(FunctionHandler(h.make_document))}

    STATIC = get_resources('statics')
    patterns = [(r"/statics/(.*)", StaticFileHandler, {"path": STATIC})]

    server = Server(apps, port=port, extra_patterns=patterns)

    if experiment._environment.maybe_jupyter():
        # in jupyter, .run_until_shutdown() may raise RuntimeError
        # because of IOLoop
        server.start()
    else:
        server.run_until_shutdown()

    DaskperimentBoard._STARTED = True
    return server


if __name__ == '__main__':
    ex = daskperiment.Experiment('bokeh_test')
    a = ex.parameter('a')

    @ex.result
    def inc(a):
        for i in range(100):
            ex.save_metric('dummy_score', epoch=i,
                           value=100 + np.random.random())
            ex.save_metric('dummy_score2', epoch=i, value=10)
        return a + 1

    ex.set_parameters(a=2)
    inc(a)

    ex.start_dashboard()
