# Browser Service

The Browser Service manages Playwright browser instances remotely using gRPC. It provides a gRPC API to start, stop, and manage browser instances that can be used by the Backend Service for browser automation tasks.

## Overview

This service allows multiple backend instances to share browser resources by managing Playwright browser servers. It supports Firefox, Chrome, and WebKit browsers, and provides CDP (Chrome DevTools Protocol) URLs for browser_use integration.

## Features

- Start/stop browser instances on demand
- Support for multiple browsers (Firefox, Chrome, WebKit)
- CDP URL generation for remote browser connections
- gRPC-based communication for better performance
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

3. Generate protobuf files (first time only):
```bash
cd ../shared
python generate_protos.py
cd ../Browser-server
```

## Configuration

### Environment Variables

```bash
BROWSER_SERVICE_HOST=localhost    # Host to bind to (default: localhost)
BROWSER_SERVICE_PORT=50051       # gRPC port (default: 50051)
```

### Default Ports

- **gRPC Service**: `50051`

## Usage

### Start the Service

**For Testing (Single Machine):**
```bash
# Run in a screen session
screen -S browser-service
python server.py
# Press Ctrl+A then D to detach
```

**For Production (Separate Machine):**
```bash
export BROWSER_SERVICE_HOST=0.0.0.0
export BROWSER_SERVICE_PORT=50051
python server.py
```

### gRPC Methods

The service exposes these gRPC methods:

#### StartBrowser
Start a browser instance.

**Request:**
```protobuf
message StartBrowserRequest {
  string browser_name = 1;  // firefox, webkit, chrome
  int32 port = 2;
}
```

**Response:**
```protobuf
message StartBrowserResponse {
  bool success = 1;
  string message = 2;
  string cdp_url = 3;
  string ws_endpoint = 4;
}
```

#### StopBrowser
Stop a browser instance.

**Request:**
```protobuf
message StopBrowserRequest {
  int32 port = 1;
}
```

#### GetBrowserConnection
Get browser connection info and CDP URL.

**Request:**
```protobuf
message GetBrowserConnectionRequest {
  int32 port = 1;
}
```

**Response:**
```protobuf
message GetBrowserConnectionResponse {
  bool running = 1;
  string cdp_url = 2;
  string ws_endpoint = 3;
  string ip = 4;
  int32 port = 5;
}
```

#### IsBrowserRunning
Check if browser is running.

**Request:**
```protobuf
message IsBrowserRunningRequest {
  int32 port = 1;
}
```

**Response:**
```protobuf
message IsBrowserRunningResponse {
  bool running = 1;
}
```

## Architecture

The service uses:
- **gRPC** for the RPC server
- **Playwright** for browser management
- **psutil** for port checking and process management

## Integration with Backend Service

The Backend Service connects to this service via gRPC to:
1. Request a browser instance (`StartBrowser`)
2. Get the CDP URL (`GetBrowserConnection`)
3. Use the remote browser for automation tasks
4. Release the browser when done (`StopBrowser`)

Example CDP URL usage in browser_use:
```python
from browser_use import Browser

browser = Browser(
    cdp_url="http://localhost:9999"  # From browser service
)
```

## Testing

### Using grpcurl

```bash
# List available services
grpcurl -plaintext localhost:50051 list

# Start browser
grpcurl -plaintext -d '{"browser_name": "firefox", "port": 9999}' \
  localhost:50051 browser_service.BrowserService/StartBrowser

# Check status
grpcurl -plaintext -d '{"port": 9999}' \
  localhost:50051 browser_service.BrowserService/IsBrowserRunning
```

## Troubleshooting

### Browser won't start
- Check if the port is already in use
- Ensure Playwright browsers are installed
- Check service logs

### Port conflicts
- Use different ports for multiple browser instances
- Check running processes: `netstat -an | grep <port>`

### Protobuf import errors
```bash
# Regenerate protobuf files
cd ../shared
python generate_protos.py
```

### Connection refused
- Verify service is running: `grpcurl -plaintext localhost:50051 list`
- Check firewall rules
- Verify port is not blocked

## Development

### Project Structure
```
Browser-server/
├── server.py              # gRPC server
├── browser_server.py      # Browser management logic
├── utils.py               # Utility functions
├── requirements.txt       # Python dependencies
├── QUICKSTART.md          # Quick start guide
└── README.md              # This file
```

### Running in Development

```bash
# Start service
python server.py

# In another terminal, test with grpcurl
grpcurl -plaintext localhost:50051 list
```

## Deployment

### Single Machine (Testing)

Run in a screen session:
```bash
screen -S browser-service
python server.py
```

### Separate Machine (Production)

1. Install dependencies
2. Configure environment variables
3. Run service: `python server.py`
4. Expose port 50051

## Quick Start

See [QUICKSTART.md](QUICKSTART.md) for a quick setup guide.

## License

Part of the Data Collector ADIA project.
