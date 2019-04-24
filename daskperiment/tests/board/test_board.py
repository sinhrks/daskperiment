import pytest

import json

import daskperiment
import daskperiment.board.board as board


@pytest.fixture
def client():
    board.app.config['TESTING'] = True
    client = board.app.test_client()

    yield client


class TestBoard(object):

    @classmethod
    def setup_class(cls):
        # TODO: setup_class
        ex = daskperiment.Experiment('test_board')
        a = ex.parameter('a')

        @ex.result
        def inc(a):
            for i in range(3):
                ex.save_metric('my_metric', epoch=i, value=a + i)
            return a + 1

        res = inc(a)

        for i in range(3):
            ex.set_parameters(a=i)
            res.compute()

        board.ex = ex
        cls.ex = ex

    @classmethod
    def teardown_class(cls):
        cls.ex._delete_cache()

    def test_html(self, client):
        response = client.get('/')
        assert response.status == '200 OK'
        assert response.data.startswith(b'<!doctype html>')

    def test_css(self, client):
        response = client.get('/static/css/style.css')
        assert response.status == '200 OK'
        assert response.data.startswith(b'html {')

    def test_get_summary_result(self, client):
        response = client.get('/json/summary/result')
        assert response.status == '200 OK'

        result = json.loads(response.data)
        exp = {'datasets': [{'borderWidth': 1, 'data': [1, 2, 3],
                             'label': 'Result'}],
               'labels': [1, 2, 3]}
        assert result == exp

    def test_get_summary_processtime(self, client):
        response = client.get('/json/summary/processtime')
        assert response.status == '200 OK'

        result = json.loads(response.data)
        assert result['labels'] == [1, 2, 3]
        assert all(d < 100 for d in result['datasets'][0]['data'])

    def test_get_table(self, client):
        response = client.get('/json/table')
        assert response.status == '200 OK'

        result = json.loads(response.data)
        assert isinstance(result, dict)
        exp_columns = [{'data': None, 'defaultContent': ''},
                       {'data': 0, 'title': 'Trial ID'},
                       {'data': 1, 'title': 'a'},
                       {'data': 2, 'title': 'Seed'},
                       {'data': 3, 'title': 'Result'},
                       {'data': 4, 'title': 'Result Type'},
                       {'data': 5, 'title': 'Success'},
                       {'data': 6, 'title': 'Finished'},
                       {'data': 7, 'title': 'Process Time'},
                       {'data': 8, 'title': 'Description'}]
        assert result['columns'] == exp_columns
        # trial id
        assert [d[0] for d in result['data']] == [1, 2, 3]
        # a
        assert [d[1] for d in result['data']] == [0, 1, 2]
        # result
        assert [d[3] for d in result['data']] == [1, 2, 3]

    @pytest.mark.parametrize('id,exp', [(1, [0, 1, 2]), (2, [1, 2, 3]),
                                        (3, [2, 3, 4])])
    def test_get_metric(self, id, exp, client):
        url = '/json/metric/?ids=[{}]&keys=["my_metric"]'
        response = client.get(url.format(id))
        assert response.status == '200 OK'

        result = json.loads(response.data)
        expected = {'datasets': [{'data': exp,
                                  'label': 'my_metric:{}'.format(id),
                                  'borderColor': '#440154',
                                  'fill': False}],
                    'labels': [0, 1, 2]}
        assert result == expected

    def test_get_metric_multi(self, client):
        url = '/json/metric/?ids=[1,2,3]&keys=["my_metric"]'
        response = client.get(url.format(id))
        assert response.status == '200 OK'

        result = json.loads(response.data)
        expected = {'datasets': [{'data': [0, 1, 2],
                                  'label': 'my_metric:1',
                                  'borderColor': '#440154',
                                  'fill': False},
                                 {'data': [1, 2, 3],
                                  'label': 'my_metric:2',
                                  'borderColor': '#208F8C',
                                  'fill': False},
                                 {'data': [2, 3, 4],
                                  'label': 'my_metric:3',
                                  'borderColor': '#FDE724',
                                  'fill': False}],
                    'labels': [0, 1, 2]}
        assert result == expected

    def test_get_code(self, client):
        response = client.get('/data/code/1')
        assert response.status == '200 OK'
        assert response.data.startswith(b'@ex.result')

        response2 = client.get('/data/code/3')
        assert response2.status == '200 OK'
        assert response2.data == response.data

    def test_get_env(self, client):
        response = client.get('/data/env/1')
        assert response.status == '200 OK'
        assert response.data.startswith(b'Platform Information:')

        response2 = client.get('/data/env/3')
        assert response2.status == '200 OK'
        assert response2.data == response.data
