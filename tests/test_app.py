from http import HTTPStatus

from fastapi.testclient import TestClient

from backend.app import app


def test_root_deve_retornar_ok_e_mensagem_da_api():
    client = TestClient(app)

    response = client.get('/')

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {'message': 'FastAPI boilerplate running.'}


def test_health_deve_retornar_status_e_database():
    client = TestClient(app)

    response = client.get('/health')

    assert response.status_code == HTTPStatus.OK
    payload = response.json()
    assert payload['status'] in {'ok', 'degraded'}
    assert payload['database'] in {'ok', 'error'}
