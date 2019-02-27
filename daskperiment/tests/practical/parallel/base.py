import threading
import time

import pandas as pd
import pandas.testing as tm


class ParallelExperimentBase(object):

    @property
    def backend(self):
        raise NotImplementedError

    def test_serial(self, ex):
        a = ex.parameter('a')

        @ex.result
        def id(a):
            ex.save_metric(metric_key='a', epoch=0, value=a)
            return a

        res = id(a)

        def compute(x):
            ex.set_parameters(a=x)
            assert res.compute() == x

        for i in range(100):
            compute(i)

        hist = ex.get_history()
        exp = pd.DataFrame({'a': range(100), 'Result': range(100)},
                           index=pd.Index(range(1, 101), name='Trial ID'),
                           columns=['a', 'Result'])
        tm.assert_frame_equal(hist[['a', 'Result']], exp)

    def test_task_parallel(self, ex):
        a = ex.parameter('a')

        @ex
        def long_task(a):
            time.sleep(0.5)
            return a

        @ex.result
        def result(a, b, c, d, e, f):
            return a + b + c + d + e + f

        res = result(long_task(a), long_task(a), long_task(a),
                     long_task(a), long_task(a), long_task(a))
        ex.set_parameters(a=1)

        # parallel
        start = time.time()
        assert res.compute() == 6
        assert time.time() - start <= 2.5

    def test_task_serial(self):
        # for comparison

        def long_task(a):
            time.sleep(0.5)
            return a

        def result(a, b, c, d, e, f):
            return a + b + c + d + e + f

        start = time.time()
        res = result(long_task(1), long_task(1), long_task(1),
                     long_task(1), long_task(1), long_task(1))
        assert res == 6
        assert time.time() - start >= 3

    def test_threading_lock(self, ex):
        a = ex.parameter('a')

        @ex.result
        def id(a):
            ex.save_metric(metric_key='a', epoch=0, value=a)
            return a

        res = id(a)

        lock = threading.Lock()

        def compute(x):
            with lock:
                # without lock, parameters may be updated
                # between set and compute

                # this test actually parallelize nothing
                ex.set_parameters(a=x)
                assert res.compute() == x

        threads = []
        for i in range(100):
            thread = threading.Thread(target=compute, args=([i]))
            threads.append(thread)

        for t in threads:
            t.start()

        for t in threads:
            t.join()

        hist = ex.get_history()

        hist = ex.get_history()
        exp = pd.DataFrame({'a': range(100), 'Result': range(100)},
                           index=pd.Index(range(1, 101), name='Trial ID'),
                           columns=['a', 'Result'])
        tm.assert_frame_equal(hist[['a', 'Result']], exp)
