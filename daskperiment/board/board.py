import pathlib

import numpy as np
import bokeh.layouts as layouts

import daskperiment
from daskperiment.board.utils import convert_columns, get_colors
from daskperiment.core.errors import TrialIDNotFoundError


# TODO: get screeninfo
WIDTH = 1200
HEIGHT = 650


def get_resources(name):
    return str(pathlib.Path(__file__).parent / name)


class DaskperimentBoard(object):

    _STARTED = False

    def __init__(self, experiment, palette='Viridis'):
        self.experiment = experiment
        self.palette = palette

    def build_layout(self):
        from bokeh.models import ColumnDataSource
        from bokeh.models.widgets import DataTable

        history = self.experiment.get_history()
        history = history.reset_index()

        source = ColumnDataSource(history)

        columns = convert_columns(history)
        dt = DataTable(source=source, columns=columns,
                       width=WIDTH, height=int(HEIGHT * 0.6))

        source.selected.on_change('indices', self.update_metric_plot)

        self.trial_ids = []
        options = self.experiment._metrics.keys()
        if len(options) > 0:
            self.metric_key = options[0]
        else:
            options = ['']
            self.metric_key = ''

        self.widgets = self.build_metric_widgets(self.metric_key, options)
        plot = self.build_metric_plot(self.metric_key, self.trial_ids)

        row = layouts.Row(self.widgets, plot)
        layout = layouts.Column(dt, row, width=WIDTH)

        self.history = history
        self.source = source
        self.layout = layout
        return self.layout

    def make_document(self, doc):
        from jinja2 import Environment, FileSystemLoader

        TEMPLATE = get_resources('templates')
        env = Environment(loader=FileSystemLoader(TEMPLATE))

        layout = self.build_layout()
        doc.template = env.get_template('index.html')
        doc.add_root(layout)
        return doc

    def update_metric_dropdown(self, attr, old, dropdown):
        self.metric_key = dropdown.value
        plot = self.build_metric_plot(self.metric_key, self.trial_ids)
        self.layout.children[1] = layouts.Row(self.widgets, plot)

    def update_metric_plot(self, attr, old, selected):
        """
        Callback to update metric plot
        """
        # mapping selected indices to trial ids
        self.trial_ids = [int(self.history['Trial ID'].iloc[i])
                          for i in selected]
        plot = self.build_metric_plot(self.metric_key, self.trial_ids)
        self.layout.children[1] = layouts.Row(self.widgets, plot)

    def build_metric_plot(self, key, trial_ids):
        from bokeh.plotting import figure

        plot = figure(width=int(WIDTH * 0.75),
                      height=int(HEIGHT * 0.35))

        if len(trial_ids) == 0:
            return plot

        colors = get_colors(self.palette, len(trial_ids))
        for i, trial_id in enumerate(trial_ids):
            try:
                # selected trial may not contain metric
                metrics = self.experiment.load_metric('dummy_score',
                                                      trial_id=trial_id)
                # cannot add multiple legend in multi_line
                plot.line(metrics.index, metrics[trial_id].values,
                          color=colors[i], legend=str(trial_id))
            except TrialIDNotFoundError:
                pass

        plot.legend.click_policy = "mute"
        return plot

    def build_metric_widgets(self, key, options):
        from bokeh.models.widgets import Select
        select = Select(title="Metric:", value=key, options=options)
        return layouts.widgetbox(select, width=int(WIDTH * 0.25))


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
        return a + 1

    ex.set_parameters(a=2)
    inc(a)

    ex.start_dashboard()
