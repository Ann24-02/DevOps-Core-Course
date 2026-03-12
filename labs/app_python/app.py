import json
import logging
import os
import platform
import socket
from datetime import datetime, timezone
from flask import Flask, jsonify, request

app = Flask(__name__)


HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', 8080))
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'


START_TIME = datetime.now(timezone.utc)


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

@app.before_request
def log_request():
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
def log_response(response):
    logger.info(
        "Request handled",
        extra={
            "extra_fields": {
                "event": "response",
                "method": request.method,
                "path": request.path,
                "status_code": response.status_code,
                "client_ip": request.remote_addr,
            }
        },
    )
    return response


@app.route('/')
def home():
    system_info = {
        'hostname': socket.gethostname(),
        'platform': platform.system(),
        'platform_version': platform.platform(),
        'architecture': platform.machine(),
        'cpu_count': os.cpu_count(),
        'python_version': platform.python_version()
    }
    
    
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
            {'path': '/health', 'method': 'GET', 'description': 'Health check'}
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