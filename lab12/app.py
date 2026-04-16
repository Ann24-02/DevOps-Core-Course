from flask import Flask, jsonify
import os
import json
import threading

app = Flask(__name__)

# Файл для хранения счетчика
DATA_DIR = os.environ.get('DATA_DIR', '/data')
COUNTER_FILE = os.path.join(DATA_DIR, 'visits.txt')
lock = threading.Lock()

def read_counter():
    """Read counter from file"""
    try:
        if os.path.exists(COUNTER_FILE):
            with open(COUNTER_FILE, 'r') as f:
                return int(f.read().strip())
    except (ValueError, IOError):
        pass
    return 0

def write_counter(count):
    """Write counter to file"""
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(COUNTER_FILE, 'w') as f:
        f.write(str(count))

@app.route('/')
def index():
    """Main endpoint - increment counter"""
    with lock:
        count = read_counter()
        count += 1
        write_counter(count)
    
    return jsonify({
        "message": "Hello from Kubernetes!",
        "visits": count
    })

@app.route('/visits')
def visits():
    """Return current visit count"""
    count = read_counter()
    return jsonify({"visits": count})

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy"})

@app.route('/config')
def config():
    """Return application configuration"""
    config_file = '/config/config.json'
    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            config = json.load(f)
        return jsonify(config)
    return jsonify({"error": "Config not found"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)