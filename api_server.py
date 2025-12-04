"""
Browser Service - HTTP REST API server for managing Playwright browser instances
Provides remote browser access for the backend service.
"""

import logging
import os
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from browser_server import (
    BROWSER_PROCESSES,
    close_browser,
    get_browser_connection,
    is_browser_running,
    start_browser,
)
from utils import get_local_ip

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Browser Service", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic models
class StartBrowserRequest(BaseModel):
    browser_name: str = "firefox"  # firefox, webkit, chrome
    port: int = 9999


class StartBrowserResponse(BaseModel):
    success: bool
    message: str
    cdp_url: Optional[str] = None
    ws_endpoint: Optional[str] = None


class StopBrowserRequest(BaseModel):
    port: int = 9999


class BrowserConnectionResponse(BaseModel):
    running: bool
    cdp_url: Optional[str] = None
    ws_endpoint: Optional[str] = None
    ip: Optional[str] = None
    port: Optional[int] = None


# API Endpoints
@app.post("/browser/start", response_model=StartBrowserResponse)
async def start_browser_endpoint(request: StartBrowserRequest):
    """Start a browser instance"""
    try:
        logger.info(f"Starting browser: {request.browser_name} on port {request.port}")
        success, message = start_browser(request.browser_name, request.port)
        
        response = StartBrowserResponse(
            success=success,
            message=message or ""
        )
        
        if success:
            # Get connection info
            conn_info = get_browser_connection(request.port)
            local_ip = get_local_ip()
            if conn_info:
                response.cdp_url = f"http://{local_ip}:{request.port}"
                response.ws_endpoint = conn_info.get("wsEndpoint", f"ws://{local_ip}:{request.port}/")
            else:
                response.cdp_url = f"http://{local_ip}:{request.port}"
                response.ws_endpoint = f"ws://{local_ip}:{request.port}/"
        
        return response
    except Exception as e:
        logger.error(f"Error starting browser: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/browser/stop")
async def stop_browser_endpoint(request: StopBrowserRequest):
    """Stop a browser instance"""
    try:
        logger.info(f"Stopping browser on port {request.port}")
        success, message = close_browser(request.port)
        
        return {
            "success": success,
            "message": message or ""
        }
    except Exception as e:
        logger.error(f"Error stopping browser: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/browser/{port}/connection", response_model=BrowserConnectionResponse)
async def get_browser_connection_endpoint(port: int):
    """Get browser connection info"""
    try:
        running = is_browser_running(port)
        
        response = BrowserConnectionResponse(running=running)
        
        if running:
            conn_info = get_browser_connection(port)
            local_ip = get_local_ip()
            response.cdp_url = f"http://{local_ip}:{port}"
            response.ws_endpoint = conn_info.get("wsEndpoint", f"ws://{local_ip}:{port}/") if conn_info else f"ws://{local_ip}:{port}/"
            response.ip = local_ip
            response.port = port
        
        return response
    except Exception as e:
        logger.error(f"Error getting browser connection: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/browser/{port}/status")
async def is_browser_running_endpoint(port: int):
    """Check if browser is running"""
    try:
        running = is_browser_running(port)
        return {"running": running}
    except Exception as e:
        logger.error(f"Error checking browser status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "browser-service"}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("BROWSER_SERVICE_PORT", "8001"))
    uvicorn.run(app, host="0.0.0.0", port=port)

