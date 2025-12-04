# Browser Service - Quick Start

Get the Browser Service running quickly for testing or production deployment.

## Prerequisites

- Python 3.11+
- Playwright browsers installed

## Quick Setup

### 1. Install Dependencies

```bash
cd Browser-server
pip install -r requirements.txt
```

### 2. Install Playwright Browsers

```bash
playwright install
```

Or if using Python's playwright:
```bash
python -m playwright install
```

### 3. Generate Protobuf Files (First Time Only)

```bash
cd ../shared
python generate_protos.py
cd ../Browser-server
```

## Running the Service

### For Testing (Single Machine)

Run in a screen session:

```bash
# Create a new screen session
screen -S browser-service

# Start the service
python server.py

# Detach: Press Ctrl+A then D
# Reattach: screen -r browser-service
```

### For Production (Separate Machine)

```bash
# Set environment variables
export BROWSER_SERVICE_HOST=0.0.0.0
export BROWSER_SERVICE_PORT=50051

# Run the service
python server.py
```

Or use a process manager like systemd, supervisor, or PM2.

## Verify Service is Running

### Check gRPC Service

```bash
# Using grpcurl (if installed)
grpcurl -plaintext localhost:50051 list
```

Expected output:
```
browser_service.BrowserService
```

### Test Service Health

The service should be listening on port `50051` (default).

## Configuration

### Environment Variables

```bash
BROWSER_SERVICE_HOST=localhost    # Host to bind to (default: localhost)
BROWSER_SERVICE_PORT=50051        # gRPC port (default: 50051)
```

### Default Ports

- **gRPC Service**: `50051`

## Service Endpoints (gRPC)

The service exposes these gRPC methods:

- `StartBrowser` - Start a browser instance
- `StopBrowser` - Stop a browser instance
- `GetBrowserConnection` - Get CDP URL and connection info
- `IsBrowserRunning` - Check if browser is running

## Troubleshooting

### Port Already in Use

```bash
# Check what's using the port
lsof -i :50051  # Linux/Mac
netstat -an | findstr 50051  # Windows

# Change port
export BROWSER_SERVICE_PORT=50052
python server.py
```

### Playwright Browsers Not Found

```bash
# Reinstall browsers
playwright install --force
```

### Protobuf Import Errors

```bash
# Regenerate protobuf files
cd ../shared
python generate_protos.py
```

## Next Steps

- See [README.md](README.md) for detailed documentation
- Configure for production deployment
- Set up monitoring and logging

