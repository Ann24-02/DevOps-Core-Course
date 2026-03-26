import pytest
import time
import re
from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_health_endpoint_structure(client):
    """Test the exact structure of health endpoint from your app."""
    response = client.get('/health')
    data = response.get_json()
    
    # Exact structure from your app.py
    assert set(data.keys()) == {'status', 'timestamp', 'uptime_seconds'}
    assert data['status'] == 'healthy'
    
    # Check timestamp is ISO format
    timestamp = data['timestamp']
    assert isinstance(timestamp, str)
    assert 'T' in timestamp  # ISO формат с T
    
    # Check uptime is non-negative integer
    assert isinstance(data['uptime_seconds'], int)
    assert data['uptime_seconds'] >= 0

def test_health_endpoint_always_healthy(client):
    """Test that health endpoint always returns healthy status."""
    # Multiple requests should all be healthy
    for _ in range(3):
        response = client.get('/health')
        assert response.get_json()['status'] == 'healthy'
        assert response.status_code == 200

def test_health_headers(client):
    """Test response headers for health endpoint."""
    response = client.get('/health')
    
    assert response.content_type == 'application/json'
    assert response.status_code == 200
    # No cache headers for health endpoint
    # Flask по умолчанию не добавляет Cache-Control
    
def test_health_uptime_consistency(client):
    """Test that uptime is consistent between root and health endpoints."""
    # Get uptime from both endpoints
    response_root = client.get('/')
    response_health = client.get('/health')
    
    uptime_root = response_root.get_json()['runtime']['uptime_seconds']
    uptime_health = response_health.get_json()['uptime_seconds']
    
    # Они должны быть очень близки (в пределах 1 секунды)
    # Из-за разницы во времени выполнения запросов
    assert abs(uptime_root - uptime_health) <= 1

def test_health_with_different_methods(client):
    """Test health endpoint only accepts GET."""
    # POST должен возвращать 405 Method Not Allowed
    response_post = client.post('/health')
    
    # Flask возвращает 405 для неразрешенных методов
    # Но может вернуть и что-то другое, зависит от конфигурации
    # Проверим что это не 200 (успех)
    assert response_post.status_code != 200
    
    # GET должен работать
    response_get = client.get('/health')
    assert response_get.status_code == 200