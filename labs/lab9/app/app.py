import json
import logging
import os
import platform
import socket
import time
import random
from datetime import datetime, timezone
from flask import Flask, jsonify, request, Response


from prometheus_client import Counter, Histogram, Gauge, generate_latest, REGISTRY

app = Flask(__name__)

HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', 8080))
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

START_TIME = datetime.now(timezone.utc)

http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint'],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10)
)

http_requests_in_progress = Gauge(
    'http_requests_in_progress',
    'Number of HTTP requests currently in progress'
)


endpoint_calls = Counter(
    'devops_info_endpoint_calls',
    'Number of calls to specific endpoints',
    ['endpoint', 'method']
)


system_info_duration = Histogram(
    'devops_info_system_collection_seconds',
    'Time taken to collect system information',
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5)
)


active_clients = Gauge(
    'devops_info_active_clients',
    'Number of active clients currently using the service'
)


service_uptime_seconds = Gauge(
    'devops_info_uptime_seconds',
    'Service uptime in seconds'
)

class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
        }

        if hasattr(record, "extra_fields") and isinstance(record.extra_fields, dict):
            log_entry.update(record.extra_fields)

        return json.dumps(log_entry, ensure_ascii=False)

logger = logging.getLogger("devops-info-service")
logger.setLevel(LOG_LEVEL)

_handler = logging.StreamHandler()
_handler.setFormatter(JSONFormatter())
logger.addHandler(_handler)
logger.propagate = False


def get_uptime():
    delta = datetime.now(timezone.utc) - START_TIME
    seconds = int(delta.total_seconds())
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    return {
        'seconds': seconds,
        'human': f"{hours} hours, {minutes} minutes"
    }

def update_uptime_metric():
    """Обновляет метрику uptime"""
    delta = datetime.now(timezone.utc) - START_TIME
    service_uptime_seconds.set(delta.total_seconds())


@app.before_request
def before_request():
    """Выполняется перед каждым запросом"""
  
    http_requests_in_progress.inc()
    
   
    if request.path == '/':
        active_clients.inc()
    

    request.start_time = time.time()
    
    logger.info(
        "Incoming request",
        extra={
            "extra_fields": {
                "event": "request",
                "method": request.method,
                "path": request.path,
                "client_ip": request.remote_addr,
                "user_agent": request.headers.get('User-Agent', 'Unknown'),
            }
        },
    )

@app.after_request
def after_request(response):
    """Выполняется после каждого запроса"""

    duration = time.time() - request.start_time
    
    
    http_requests_total.labels(
        method=request.method, 
        endpoint=request.path, 
        status=response.status_code
    ).inc()
    
   
    http_request_duration_seconds.labels(
        method=request.method, 
        endpoint=request.path
    ).observe(duration)
    
    http_requests_in_progress.dec()
    

    if request.path == '/':
        active_clients.dec()
    
    logger.info(
        "Request handled",
        extra={
            "extra_fields": {
                "event": "response",
                "method": request.method,
                "path": request.path,
                "status_code": response.status_code,
                "duration_seconds": duration,
                "client_ip": request.remote_addr,
            }
        },
    )
    return response

@app.route('/metrics')
def metrics():
    """Эндпоинт для сбора метрик Prometheus"""
 
    update_uptime_metric()
    
    logger.info(
        "Metrics endpoint accessed",
        extra={
            "extra_fields": {
                "event": "metrics_scrape",
                "client_ip": request.remote_addr,
            }
        },
    )
    
    return Response(generate_latest(REGISTRY), mimetype="text/plain")


@app.route('/')
def home():
    """Главный эндпоинт с информацией о сервисе"""
    
    endpoint_calls.labels(endpoint='/', method='GET').inc()
    

    start_time = time.time()
    
   
    time.sleep(random.uniform(0.01, 0.1))
    
    system_info = {
        'hostname': socket.gethostname(),
        'platform': platform.system(),
        'platform_version': platform.platform(),
        'architecture': platform.machine(),
        'cpu_count': os.cpu_count(),
        'python_version': platform.python_version()
    }
    
  
    system_info_duration.observe(time.time() - start_time)
    
    uptime = get_uptime()
    runtime_info = {
        'uptime_seconds': uptime['seconds'],
        'uptime_human': uptime['human'],
        'current_time': datetime.now(timezone.utc).isoformat(),
        'timezone': 'UTC'
    }
    
    request_info = {
        'client_ip': request.remote_addr,
        'user_agent': request.headers.get('User-Agent', 'Unknown'),
        'method': request.method,
        'path': request.path
    }
    
    response = {
        'service': {
            'name': 'devops-info-service',
            'version': '1.0.0',
            'description': 'DevOps course info service',
            'framework': 'Flask'
        },
        'system': system_info,
        'runtime': runtime_info,
        'request': request_info,
        'endpoints': [
            {'path': '/', 'method': 'GET', 'description': 'Service information'},
            {'path': '/health', 'method': 'GET', 'description': 'Health check'},
            {'path': '/metrics', 'method': 'GET', 'description': 'Prometheus metrics'}
        ]
    }

    logger.info(
        "Home endpoint served",
        extra={
            "extra_fields": {
                "event": "home",
                "client_ip": request.remote_addr,
            }
        },
    )

    return jsonify(response)

@app.route('/health')
def health():
    """Эндпоинт для проверки здоровья сервиса"""
   
    endpoint_calls.labels(endpoint='/health', method='GET').inc()
    
    uptime = get_uptime()
    payload = {
        'status': 'healthy',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'uptime_seconds': uptime['seconds']
    }

    logger.info(
        "Health check",
        extra={
            "extra_fields": {
                "event": "health",
                "client_ip": request.remote_addr,
                "uptime_seconds": uptime['seconds'],
            }
        },
    )

    return jsonify(payload)


@app.errorhandler(404)
def not_found(error):
    """Обработчик 404 ошибки"""
   
    if not hasattr(request, 'start_time'):
        request.start_time = time.time()
    
    logger.warning(
        "Not found",
        extra={
            "extra_fields": {
                "event": "error_404",
                "path": request.path,
                "client_ip": request.remote_addr,
            }
        },
    )

    return jsonify({
        'error': 'Not Found',
        'message': 'Endpoint does not exist'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """Обработчик 500 ошибки"""
    
    if not hasattr(request, 'start_time'):
        request.start_time = time.time()
    
    logger.error(
        "Internal server error",
        extra={
            "extra_fields": {
                "event": "error_500",
                "path": request.path,
                "client_ip": request.remote_addr,
            }
        },
    )

    return jsonify({
        'error': 'Internal Server Error',
        'message': 'An unexpected error occurred'
    }), 500


if __name__ == '__main__':
    logger.info(
        "Starting DevOps Info Service",
        extra={
            "extra_fields": {
                "event": "startup",
                "host": HOST,
                "port": PORT,
                "debug": DEBUG,
            }
        },
    )
    app.run(host=HOST, port=PORT, debug=DEBUG)
# Version: v2 - четверг, 26 марта 2026 г. 19:07:48 (MSK)
