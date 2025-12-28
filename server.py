import asyncio
import logging
import os
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
try:
    import browser_service_pb2
    import browser_service_pb2_grpc
    PROTOBUF_AVAILABLE = True
except ImportError:
    logging.warning("Protobuf files not found. Using placeholder classes.")
    PROTOBUF_AVAILABLE = False

# Placeholder classes for fallback
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


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)


class BrowserServiceServicer(browser_service_pb2_grpc.BrowserServiceServicer if PROTOBUF_AVAILABLE else object):
    """gRPC servicer for Browser Service"""
    
    def StartBrowser(self, request, context):
        """Start a browser instance"""
        try:
            browser_name = request.browser_name or "chrome"
            port = request.port or 9999
            
            logger.info(f"Starting browser: {browser_name} on port {port}")
            success, used_port, message = start_browser(browser_name, port)
            
            response = browser_service_pb2.StartBrowserResponse() if PROTOBUF_AVAILABLE else StartBrowserResponse()
            response.success = success
            response.message = message or ""
            
            if success:
                # Get connection info using the ACTUAL port used
                conn_info = get_browser_connection(used_port)
                if conn_info:
                    response.cdp_url = conn_info.get("cdp_url", "")
                    response.ws_endpoint = conn_info.get("ws_endpoint", "")
                else:
                    ip = "127.0.0.1"
                    response.cdp_url = f"ws://{ip}:{used_port}/"
                    response.ws_endpoint = f"ws://{ip}:{used_port}/"
            
            return response
        except Exception as e:
            logger.error(f"Error starting browser: {e}", exc_info=True)
            response = browser_service_pb2.StartBrowserResponse() if PROTOBUF_AVAILABLE else StartBrowserResponse()
            response.success = False
            response.message = str(e)
            return response
    
    def StopBrowser(self, request, context):
        """Stop a browser instance"""
        try:
            port = request.port or 9999
            logger.info(f"Stopping browser on port {port}")
            
            success, message = close_browser(port)
            
            response = browser_service_pb2.StopBrowserResponse() if PROTOBUF_AVAILABLE else StopBrowserResponse()
            response.success = success
            response.message = message or ""
            return response
        except Exception as e:
            logger.error(f"Error stopping browser: {e}", exc_info=True)
            response = browser_service_pb2.StopBrowserResponse() if PROTOBUF_AVAILABLE else StopBrowserResponse()
            response.success = False
            response.message = str(e)
            return response
    
    def GetBrowserConnection(self, request, context):
        """Get browser connection info"""
        try:
            port = request.port or 9999
            running = is_browser_running(port)
            
            response = browser_service_pb2.GetBrowserConnectionResponse() if PROTOBUF_AVAILABLE else GetBrowserConnectionResponse()
            response.running = running
            
            if running:
                conn_info = get_browser_connection(port)
                if conn_info:
                    response.cdp_url = conn_info.get("cdp_url", "")
                    response.ws_endpoint = conn_info.get("ws_endpoint", "")
                    response.ip = conn_info.get("ip", "")
                    response.port = conn_info.get("port", port)
                else:
                    ip = "127.0.0.1"
                    response.cdp_url = f"ws://{ip}:{port}/"
                    response.ws_endpoint = f"ws://{ip}:{port}/"
                    response.ip = ip
                    response.port = port
            
            return response
        except Exception as e:
            logger.error(f"Error getting browser connection: {e}", exc_info=True)
            response = browser_service_pb2.GetBrowserConnectionResponse() if PROTOBUF_AVAILABLE else GetBrowserConnectionResponse()
            response.running = False
            return response
    
    def IsBrowserRunning(self, request, context):
        """Check if browser is running"""
        try:
            port = request.port or 9999
            running = is_browser_running(port)
            
            response = browser_service_pb2.IsBrowserRunningResponse() if PROTOBUF_AVAILABLE else IsBrowserRunningResponse()
            response.running = running
            return response
        except Exception as e:
            logger.error(f"Error checking browser status: {e}", exc_info=True)
            response = browser_service_pb2.IsBrowserRunningResponse() if PROTOBUF_AVAILABLE else IsBrowserRunningResponse()
            response.running = False
            return response


def serve(port: int = 50061):
    """Start the gRPC server"""
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    
    # Add servicer
    servicer = BrowserServiceServicer()
    try:
        browser_service_pb2_grpc.add_BrowserServiceServicer_to_server(servicer, server)
    except Exception as e:
        logger.warning(f"Could not add servicer to server: {e}")
    
    listen_addr = f"0.0.0.0:{port}"
    server.add_insecure_port(listen_addr)
    server.start()
    
    logger.info(f"Browser Service gRPC server started on {listen_addr}")
    
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        logger.info("Shutting down Browser Service...")
        server.stop(grace=5)


if __name__ == "__main__":
    port = int(os.getenv("BROWSER_SERVICE_PORT", "50061"))
    serve(port)

