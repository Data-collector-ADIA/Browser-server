"""
Browser Service - gRPC server for managing Playwright browser instances
Provides remote browser access for the backend service.
"""

import asyncio
import logging
from concurrent import futures
from typing import Optional

import grpc
from browser_server import (
    BROWSER_PROCESSES,
    close_browser,
    get_browser_connection,
    is_browser_running,
    start_browser,
)
from utils import get_local_ip

# Import generated protobuf code
# Note: You'll need to generate these from the .proto files
# python -m grpc_tools.protoc -I../shared/protos --python_out=. --grpc_python_out=. browser_service.proto

# For now, we'll create a placeholder structure
# You'll need to generate the actual protobuf Python code
try:
    import browser_service_pb2
    import browser_service_pb2_grpc
except ImportError:
    # Fallback: We'll create simple message classes
    logging.warning("Protobuf files not found. Using placeholder classes.")
    
    class StartBrowserRequest:
        def __init__(self):
            self.browser_name = ""
            self.port = 9999
    
    class StartBrowserResponse:
        def __init__(self):
            self.success = False
            self.message = ""
            self.cdp_url = ""
            self.ws_endpoint = ""
    
    class StopBrowserRequest:
        def __init__(self):
            self.port = 9999
    
    class StopBrowserResponse:
        def __init__(self):
            self.success = False
            self.message = ""
    
    class GetBrowserConnectionRequest:
        def __init__(self):
            self.port = 9999
    
    class GetBrowserConnectionResponse:
        def __init__(self):
            self.running = False
            self.cdp_url = ""
            self.ws_endpoint = ""
            self.ip = ""
            self.port = 0
    
    class IsBrowserRunningRequest:
        def __init__(self):
            self.port = 9999
    
    class IsBrowserRunningResponse:
        def __init__(self):
            self.running = False

    class BrowserServiceServicer:
        pass

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)


class BrowserServiceServicer:
    """gRPC servicer for Browser Service"""
    
    def StartBrowser(self, request, context):
        """Start a browser instance"""
        try:
            browser_name = request.browser_name or "firefox"
            port = request.port or 9999
            
            logger.info(f"Starting browser: {browser_name} on port {port}")
            success, message = start_browser(browser_name, port)
            
            response = StartBrowserResponse()
            response.success = success
            response.message = message or ""
            
            if success:
                # Get connection info
                conn_info = get_browser_connection(port)
                if conn_info:
                    local_ip = get_local_ip()
                    # CDP URL format: http://ip:port
                    response.cdp_url = f"http://{local_ip}:{port}"
                    response.ws_endpoint = conn_info.get("wsEndpoint", "")
                else:
                    response.cdp_url = f"http://{get_local_ip()}:{port}"
                    response.ws_endpoint = f"ws://{get_local_ip()}:{port}/"
            
            return response
        except Exception as e:
            logger.error(f"Error starting browser: {e}", exc_info=True)
            response = StartBrowserResponse()
            response.success = False
            response.message = str(e)
            return response
    
    def StopBrowser(self, request, context):
        """Stop a browser instance"""
        try:
            port = request.port or 9999
            logger.info(f"Stopping browser on port {port}")
            
            success, message = close_browser(port)
            
            response = StopBrowserResponse()
            response.success = success
            response.message = message or ""
            return response
        except Exception as e:
            logger.error(f"Error stopping browser: {e}", exc_info=True)
            response = StopBrowserResponse()
            response.success = False
            response.message = str(e)
            return response
    
    def GetBrowserConnection(self, request, context):
        """Get browser connection info"""
        try:
            port = request.port or 9999
            running = is_browser_running(port)
            
            response = GetBrowserConnectionResponse()
            response.running = running
            
            if running:
                conn_info = get_browser_connection(port)
                local_ip = get_local_ip()
                response.cdp_url = f"http://{local_ip}:{port}"
                response.ws_endpoint = conn_info.get("wsEndpoint", "") if conn_info else f"ws://{local_ip}:{port}/"
                response.ip = local_ip
                response.port = port
            
            return response
        except Exception as e:
            logger.error(f"Error getting browser connection: {e}", exc_info=True)
            response = GetBrowserConnectionResponse()
            response.running = False
            return response
    
    def IsBrowserRunning(self, request, context):
        """Check if browser is running"""
        try:
            port = request.port or 9999
            running = is_browser_running(port)
            
            response = IsBrowserRunningResponse()
            response.running = running
            return response
        except Exception as e:
            logger.error(f"Error checking browser status: {e}", exc_info=True)
            response = IsBrowserRunningResponse()
            response.running = False
            return response


def serve(port: int = 50051):
    """Start the gRPC server"""
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    
    # Add servicer
    servicer = BrowserServiceServicer()
    try:
        browser_service_pb2_grpc.add_BrowserServiceServicer_to_server(servicer, server)
    except NameError:
        logger.warning("Using placeholder servicer (protobuf files not generated)")
        # In production, you must generate protobuf files first
    
    listen_addr = f"[::]:{port}"
    server.add_insecure_port(listen_addr)
    server.start()
    
    logger.info(f"Browser Service gRPC server started on {listen_addr}")
    
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        logger.info("Shutting down Browser Service...")
        server.stop(grace=5)


if __name__ == "__main__":
    import os
    port = int(os.getenv("BROWSER_SERVICE_PORT", "50051"))
    serve(port)

