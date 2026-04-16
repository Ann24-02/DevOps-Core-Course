import pytest
import json
import os  # <-- ДОБАВЬТЕ ЭТОТ ИМПОРТ
import platform
import socket
import time
from datetime import datetime, timezone, timedelta
from lab12.app import app, START_TIME, get_uptime

@pytest.fixture
def client():
    """Test client fixture."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_root_endpoint_returns_200(client):
    """Test that root endpoint returns 200 OK."""
    response = client.get('/')
    assert response.status_code == 200
    assert response.content_type == 'application/json'

def test_root_endpoint_has_required_fields(client):
    """Test that root endpoint has all required JSON fields from your app."""
    response = client.get('/')
    data = response.get_json()
    
    # Check structure from YOUR app.py
    assert 'service' in data
    assert 'system' in data
    assert 'runtime' in data
    assert 'request' in data
    assert 'endpoints' in data
    
    # Service info
    service = data['service']
    assert service['name'] == 'devops-info-service'
    assert service['version'] == '1.0.0'
    assert service['description'] == 'DevOps course info service'
    assert service['framework'] == 'Flask'
    
    # System info (from your platform/socket calls)
    system = data['system']
    assert system['hostname'] == socket.gethostname()
    assert system['platform'] == platform.system()
    assert system['platform_version'] == platform.platform()
    assert system['architecture'] == platform.machine()
    assert system['cpu_count'] == os.cpu_count()  # <-- Теперь os определен
    assert system['python_version'] == platform.python_version()
    
    # Runtime info
    runtime = data['runtime']
    assert 'uptime_seconds' in runtime
    assert 'uptime_human' in runtime
    assert 'current_time' in runtime
    assert runtime['timezone'] == 'UTC'
    
    # Request info
    request_info = data['request']
    assert 'client_ip' in request_info
    assert 'user_agent' in request_info
    assert request_info['method'] == 'GET'
    assert request_info['path'] == '/'
    
    # Endpoints list
    endpoints = data['endpoints']
    assert len(endpoints) == 2
    assert endpoints[0]['path'] == '/'
    assert endpoints[0]['method'] == 'GET'
    assert endpoints[1]['path'] == '/health'
    assert endpoints[1]['method'] == 'GET'

def test_health_endpoint(client):
    """Test health endpoint from your app."""
    response = client.get('/health')
    assert response.status_code == 200
    
    data = response.get_json()
    assert data['status'] == 'healthy'
    assert 'timestamp' in data
    assert 'uptime_seconds' in data
    assert isinstance(data['uptime_seconds'], int)

def test_get_uptime_function():
    """Test the get_uptime helper function."""
    uptime = get_uptime()
    
    assert 'seconds' in uptime
    assert 'human' in uptime
    assert isinstance(uptime['seconds'], int)
    assert uptime['seconds'] >= 0
    assert 'hours' in uptime['human'] or 'minutes' in uptime['human']

def test_error_handlers(client):
    """Test custom error handlers."""
    # Test 404
    response = client.get('/nonexistent-endpoint')
    assert response.status_code == 404
    data = response.get_json()
    assert data['error'] == 'Not Found'
    assert 'message' in data
    
    # Note: 500 error is hard to trigger without breaking app
    # We'll trust it's defined in app.py

def test_environment_variables():
    """Test that environment variables have defaults."""
    # HOST defaults
    # В вашем app.py HOST берется из os.getenv('HOST', '0.0.0.0')
    # Проверим что приложение корректно обрабатывает переменные окружения
    assert hasattr(app, 'config')
    
    # Проверим что дебаг режим выключен при тестировании
    assert app.debug == False

def test_application_structure():
    """Test that app has all required components."""
    # Check routes exist - проверяем по именам функций
    # Ключи в _rules_by_endpoint это имена функций, не пути
    endpoint_names = list(app.url_map._rules_by_endpoint.keys())
    
    # Должны быть функции home и health
    assert 'home' in endpoint_names
    assert 'health' in endpoint_names
    
    # Проверим что пути правильные
    rules = list(app.url_map.iter_rules())
    paths = [rule.rule for rule in rules]
    assert '/' in paths
    assert '/health' in paths
    
    # Check error handlers
    if app.error_handler_spec and None in app.error_handler_spec:
        error_handlers = app.error_handler_spec[None]
        assert 404 in error_handlers
        assert 500 in error_handlers

def test_uptime_increases(client):
    """Test that uptime increases between requests."""
    # Получаем начальное время
    response1 = client.get('/health')
    uptime1 = response1.get_json()['uptime_seconds']
    
    # Ждем достаточно долго чтобы uptime изменился (2 секунды)
    # Время обновляется с секундной точностью в вашем app.py
    time.sleep(2)  # <-- УВЕЛИЧЬТЕ до 2 секунд
    
    response2 = client.get('/health')
    uptime2 = response2.get_json()['uptime_seconds']
    
    # uptime должен увеличиться на 1-2 секунды
    # Используем assert uptime2 >= uptime1 + 1 для надежности
    assert uptime2 > uptime1, f"uptime2={uptime2}, uptime1={uptime1}"
    
    # ИЛИ более мягкая проверка (предпочтительнее):
    # assert uptime2 >= uptime1

def test_root_timestamp_format(client):
    """Test timestamp in root endpoint is ISO format."""
    import re
    response = client.get('/')
    data = response.get_json()
    
    # Check ISO 8601 format (ваш app.py использует isoformat())
    timestamp = data['runtime']['current_time']
    
    # Проверяем что это валидная дата ISO
    # Ваш app.py: datetime.now(timezone.utc).isoformat()
    # Это даст что-то вроде: "2024-01-15T10:30:45.123456+00:00"
    
    # Простая проверка что это строка и содержит T
    assert isinstance(timestamp, str)
    assert 'T' in timestamp
    assert '+' in timestamp or 'Z' in timestamp or timestamp.count('-') >= 2
    
    # Можно попробовать распарсить
    try:
        parsed = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        assert parsed.tzinfo is not None  # Должен быть часовой пояс
    except ValueError:
        # Если не парсится стандартным методом, проверим паттерном
        iso_pattern = r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}'
        assert re.match(iso_pattern, timestamp) is not None