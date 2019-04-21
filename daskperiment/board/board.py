import html
import json

from flask import Flask,  jsonify, render_template, request

import numpy as np
import pandas as pd

import daskperiment


app = Flask(__name__)


@app.route('/')
def summary():
    title = 'Experiment: {}'.format(ex.id)
    metric_names = ex._metrics.keys()
    if len(metric_names) == 0:
        metric_names = ['']

    return render_template('index.html',
                           title=title,
                           metric_names=metric_names)


def maybe_escape(s):
    try:
        return html.escape(s)
    except Exception:
        s


@app.route('/json/summary/<label>')
def get_summary(label):
    mapper = {'result': 'Result', 'processtime': 'Process Time'}
    label = mapper[label]
    df = ex.get_history(verbose=True)

    data = df[label]
    json_index = data.index.to_series().to_json(orient='values')
    json_data = data.to_json(orient='values')

    data = {'labels': json.loads(json_index),
            'datasets': [{'label': label,
                          'data': json.loads(json_data),
                          'borderWidth': 1}]}
    return jsonify(data)


@app.route('/json/table')
def get_table():
    df = ex.get_history(verbose=True)
    df = df.reset_index(drop=False)
    # perform formatting on server side
    df['Finished'] = df['Finished'].dt.strftime("%Y-%m-%d %H:%M:%S")

    # TODO: list up string dtype and escape
    df['Result Type'] = df['Result Type'].map(maybe_escape)
    df['Description'] = df['Description'].map(maybe_escape)

    json_data = json.loads(df.to_json(orient="split"))

    columns = [{"title": str(col), 'data': i} for (i, col) in
               enumerate(json_data["columns"])]

    # dummy for checkbox, is there better way?
    columns = [{"data": None, 'defaultContent': ''}] + columns
    return jsonify(data=json_data["data"], columns=columns)


@app.route('/json/metric/')
def get_metric():

    ids = json.loads(request.args.get('ids'))
    keys = json.loads(request.args.get('keys'))

    # TODO: move to Experiment.load_metric
    metrics = []
    for key in keys:
        try:
            metric = ex.load_metric(key, trial_id=ids)
            metric.columns = [key + ':{}'.format(c) for c in metric.columns]
            metrics.append(metric)
        except Exception:
            pass
    if len(metrics) == 0:
        data = {'labels': [], 'datasets': []}
        return jsonify(data)

    metrics = pd.concat(metrics, axis=1)
    json_index = metrics.index.to_series().to_json(orient='values')
    datasets = []
    for name, col in metrics.iteritems():
        json_data = col.to_json(orient='values')
        datasets.append({'label': name,
                         'data': json.loads(json_data)})

    data = {'labels': json.loads(json_index),
            'datasets': datasets}
    return jsonify(data)


@app.route('/data/code/<int:id>')
def get_code(id):
    code = ex.get_code(trial_id=id)
    return code


@app.route('/data/env/<int:id>')
def get_env(id):
    env = ex.get_environment(trial_id=id)
    return env


def maybe_start_dashboard(experiment, port=5000, blocking=None,
                          debug=False):
    global ex
    ex = experiment

    if blocking is None:
        if experiment._environment.maybe_jupyter():
            blocking = False
        else:
            blocking = True
    if blocking:
        app.run(host='0.0.0.0', port=port, debug=debug)
    else:
        import threading
        threading.Thread(target=app.run,
                         kwargs=dict(host='0.0.0.0', port=port,
                                     debug=debug))


if __name__ == "__main__":
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

    maybe_start_dashboard(ex, debug=True)
