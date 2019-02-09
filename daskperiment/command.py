import click

import daskperiment


@click.command()
@click.option('--port', default=5000)
@click.argument('experiment')
def board(port, experiment):
    ex = daskperiment.Experiment(experiment)
    ex.start_dashboard(port=port)
