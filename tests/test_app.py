import pytest
from page_analyzer.app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_index_route(client):
    response = client.get('/')
    
    assert response.status_code == 200
    
    assert b"Hello, World!" in response.data
    
    assert response.content_type == 'text/html; charset=utf-8'