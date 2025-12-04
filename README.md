# Browser Service

The Browser Service manages Playwright browser instances remotely. It provides an HTTP REST API to start, stop, and manage browser instances that can be used by the Backend Service for browser automation tasks.

## Overview

This service allows multiple backend instances to share browser resources by managing Playwright browser servers. It supports Firefox, Chrome, and WebKit browsers, and provides CDP (Chrome DevTools Protocol) URLs for browser_use integration.

## Features

- Start/stop browser instances on demand
- Support for multiple browsers (Firefox, Chrome, WebKit)
- CDP URL generation for remote browser connections
- Health check endpoints
- Process management and cleanup

## Installation

### Prerequisites

- Python 3.11 or higher
- Playwright browsers installed

### Setup

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Install Playwright browsers:
```bash
playwright install
```

3. Create logs directory:
```bash
mkdir -p logs
```

## Configuration

Set environment variables (optional):

```bash
BROWSER_SERVICE_PORT=8001  # Default: 8001
```

## Usage

### Start the Service

```bash
python api_server.py
```

Or with custom port:
```bash
BROWSER_SERVICE_PORT=8001 python api_server.py
```

The service will start on `http://localhost:8001` by default.

### API Endpoints

#### Health Check
```bash
GET /health
```
Returns service health status.

#### Start Browser
```bash
POST /browser/start
Content-Type: application/json

{
  "browser_name": "firefox",  // firefox, chrome, webkit
  "port": 9999
}
```

Response:
```json
{
  "success": true,
  "message": "",
  "cdp_url": "http://localhost:9999",
  "ws_endpoint": "ws://localhost:9999/"
}
```

#### Stop Browser
```bash
POST /browser/stop
Content-Type: application/json

{
  "port": 9999
}
```

#### Get Browser Connection
```bash
GET /browser/{port}/connection
```

Returns:
```json
{
  "running": true,
  "cdp_url": "http://localhost:9999",
  "ws_endpoint": "ws://localhost:9999/",
  "ip": "192.168.1.100",
  "port": 9999
}
```

#### Check Browser Status
```bash
GET /browser/{port}/status
```

Returns:
```json
{
  "running": true
}
```

## Architecture

The service uses:
- **FastAPI** for the REST API server
- **Playwright** for browser management
- **psutil** for port checking and process management

## Integration with Backend Service

The Backend Service connects to this service to:
1. Request a browser instance
2. Get the CDP URL for browser_use
3. Use the remote browser for automation tasks
4. Release the browser when done

Example CDP URL usage in browser_use:
```python
from browser_use import Browser

browser = Browser(
    cdp_url="http://localhost:9999"  # From browser service
)
```

## Troubleshooting

### Browser won't start
- Check if the port is already in use
- Ensure Playwright browsers are installed
- Check logs in `logs/browser.log`

### Port conflicts
- Use different ports for multiple browser instances
- Check running processes: `netstat -an | grep <port>`

## Development

### Project Structure
```
Browser-server/
├── api_server.py      # FastAPI HTTP server
├── browser_server.py  # Browser management logic
├── utils.py           # Utility functions
├── requirements.txt   # Python dependencies
└── README.md         # This file
```

### Testing

Test the service endpoints:
```bash
# Health check
curl http://localhost:8001/health

# Start browser
curl -X POST http://localhost:8001/browser/start \
  -H "Content-Type: application/json" \
  -d '{"browser_name": "firefox", "port": 9999}'

# Check status
curl http://localhost:8001/browser/9999/status
```

## License

Part of the Data Collector ADIA project.
