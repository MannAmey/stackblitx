import pytest
from app import create_app

@pytest.fixture
def app():
    app, socketio = create_app()
    app.config['TESTING'] = True
    return app

@pytest.fixture
def client(app):
    return app.test_client()

def test_health_endpoint(client):
    """Test the health check endpoint"""
    response = client.get('/api/health')
    assert response.status_code == 200
    
    data = response.get_json()
    assert data['status'] == 'healthy'
    assert 'timestamp' in data
    assert 'version' in data

def test_404_handler(client):
    """Test 404 error handler"""
    response = client.get('/nonexistent-endpoint')
    assert response.status_code == 404
    
    data = response.get_json()
    assert data['success'] is False
    assert 'not found' in data['error'].lower()