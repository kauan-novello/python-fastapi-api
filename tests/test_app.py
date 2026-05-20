from http import HTTPStatus

from fastapi.testclient import TestClient

from backend.app import app


def test_root_deve_retornar_ok_e_mensagem_da_api():
    client = TestClient(app)  # Arrange

    response = client.get('/')  # Act

    assert response.status_code == HTTPStatus.OK  # Assert
    assert response.json() == {
        'message': 'FastAPI boilerplate running.'
    }  # Assert


def test_health_deve_retornar_ok():
    client = TestClient(app)

    response = client.get('/health')

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {'status': 'ok'}
