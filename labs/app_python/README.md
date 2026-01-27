# DevOps Info Service

A web service that provides system information and health status for DevOps monitoring.

## Features
- Complete system information (OS, hardware, Python version)
- Health check endpoint for monitoring
- Self-documenting API
- Configurable via environment variables

## Prerequisites
- Python 3.11 or higher
- pip package manager

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd app_python 
```
## Create virtual environment:
python -m venv venv
source venv/bin/activate  # On Mac/Linux
# or
venv\Scripts\activate     # On Windows 

## Install dependencies:
pip install -r requirements.txt

## Running the Application
- Default configuration: python app.py
- Server starts at: http://localhost:5000
- Custom port: PORT=8080 python app.py
- Custom host and port: HOST=127.0.0.1 PORT=3000 python app.py

## API Endpoints 
- GET /
Returns comprehensive service and system information.
- GET /health
Health check endpoint for monitoring.

## Project structure 
app_python/
├── app.py              # Main application
├── requirements.txt    # Python dependencies
├── README.md          # This documentation
├── .gitignore         # Git ignore rules
├── docs/              # Lab documentation
│   ├── LAB01.md
│   └── screenshots/        # Proof of work
        ├── 01-main-endpoint.png
        ├── 02-health-check.png
        └── 03-formatted-output.png
└── tests/             # Unit tests
    └── __init__.py 