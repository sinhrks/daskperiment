from abc import abstractmethod

import bokeh.layouts as layouts
from bokeh.models.widgets import Panel, Select
from bokeh.models.widgets.markups import PreText
from bokeh.plotting import figure

from daskperiment.board.utils import get_colors
from daskperiment.core.errors import TrialIDNotFoundError


_PLOT_HEIGHT = 0.35


class _PanelFactory(object):

    def __init__(self, board):
        self.board = board

    @abstractmethod
    def build_widget(self):
        raise NotImplementedError

    def build_blank_figure(self):
        return figure(height=int(self.board.height * _PLOT_HEIGHT),
                      width=self.board.width,
                      sizing_mode='scale_width')

    @abstractmethod
    def build_content(self):
        raise NotImplementedError

    def build(self):
        widget = self.build_widget()
        content = self.build_content()

        contents = [c for c in [widget, content] if c is not None]

        self.layout = layouts.layout(contents)
        return Panel(child=self.layout, title=self.NAME)


class SummaryPanel(_PanelFactory):

    NAME = 'Summary'

    def build_widget(self):
        options = ['Result', 'Process Time']
        self.key = options[0]

        select = Select(value=self.key, options=options)
        select.on_change('value', self.callback_select)
        return layouts.widgetbox(select, sizing_mode='scale_width')

    def build_content(self):
        plot = self.build_blank_figure()
        history = self.board.history
        # TODO: handle parameter colides
        plot.vbar(x=history['Trial ID'], width=0.8,
                  top=history[self.key])
        return plot

    def update_content(self):
        plot = self.build_content()
        self.layout.children[1] = plot
        return plot

    def callback_select(self, attr, old, new):
        self.key = new
        self.update_content()


class MetricPanel(_PanelFactory):

    NAME = 'Metric'

    def build_widget(self):
        options = self.board.experiment._metrics.keys()
        if len(options) > 0:
            self.key = options[0]
        else:
            options = ['']
            self.key = ''

        select = Select(title="Metric:", value=self.key, options=options)
        select.on_change('value', self.callback_select)
        return layouts.widgetbox(select, sizing_mode='scale_width')

    def build_content(self):
        return self.build_blank_figure()

    def update_content(self):
        plot = self.build_blank_figure()
        trial_ids = self.board.trial_ids

        if len(trial_ids) == 0:
            # TODO: do not return here?
            return plot

        colors = get_colors(self.board.palette, len(trial_ids))
        for i, trial_id in enumerate(trial_ids):
            try:
                # selected trial may not contain metric
                metrics = self.board.experiment.load_metric(self.key,
                                                            trial_id=trial_id)
                # cannot add multiple legend in multi_line
                plot.line(metrics.index, metrics[trial_id].values,
                          color=colors[i], legend=str(trial_id))
            except TrialIDNotFoundError:
                pass
        if len(trial_ids) > 0:
            plot.legend.click_policy = "mute"
        self.layout.children[1] = plot
        return plot

    def callback_select(self, attr, old, new):
        self.key = new
        self.update_content()


class CodePanel(_PanelFactory):

    NAME = 'Code'

    def build_widget(self):
        return None

    def build_content(self):
        trial_ids = self.board.trial_ids
        if len(trial_ids) > 0:
            env = self.board.experiment.get_code(trial_id=trial_ids[-1])
            return PreText(text=env, width=self.board.width)
        else:
            return PreText(text='', width=self.board.width)

    def update_content(self):
        content = self.build_content()
        self.layout.children[0] = content
        return content


class EnvironmentPanel(_PanelFactory):

    NAME = 'Environment'

    def build_widget(self):
        options = self.board.experiment._environment.keys()
        self.key = options[0]

        select = Select(value=self.key, options=options)
        select.on_change('value', self.callback_select)
        return layouts.widgetbox(select, sizing_mode='scale_width')

    def build_content(self):
        trial_ids = self.board.trial_ids
        if len(trial_ids) > 0:
            env = self.board.experiment.get_environment(trial_id=trial_ids[-1],
                                                        category=self.key)
            return PreText(text=env, width=self.board.width)
        else:
            return PreText(text='', width=self.board.width)

    def update_content(self):
        content = self.build_content()
        self.layout.children[1] = content
        return content

    def callback_select(self, attr, old, new):
        self.key = new
        self.update_content()
