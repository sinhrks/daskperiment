import random
import numpy as np

import daskperiment

ex = daskperiment.Experiment(id='random_experiment_pj')


@ex.result
def random_result():
    res = np.random.random() + random.random()
    print(res)
    return res


random_result()

print(ex.get_history())
