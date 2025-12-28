import subprocess
import logging
import os
import tempfile
import shutil
import time
from utils import get_local_ip, is_port_in_use
from playwright.sync_api import sync_playwright

logging.basicConfig(
    filename="logs/browser.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

BROWSER_PROCESSES = {}  # port → {process: Popen, user_data_dir: str}


def get_browser_executable_path(browser_name="firefox"):
    """Get the executable path for a browser using Playwright."""
    try:
        # Map chrome to chromium for playwright if needed
        if browser_name == "chrome":
            browser_name = "chromium"
            
        with sync_playwright() as p:
            browser_type = getattr(p, browser_name)
            return browser_type.executable_path
    except Exception as e:
        logging.error(f"Failed to get browser executable path for {browser_name}: {e}")
        return None


def start_browser(browser_name="chrome", port=9999):
    try:
        if browser_name not in ["firefox", "webkit", "chrome", "chromium"]:
            return False, port, f"Invalid browser: {browser_name}"

        # Reserved ports to avoid (service ports)
        reserved_ports = range(50050, 50062)
        
        # Find next available port if current is in use or reserved
        original_port = port
        while is_port_in_use(port) or port in reserved_ports:
            port += 1
            if port > original_port + 100: # Limit retry range
                return False, original_port, "Could not find an available port within range"
        
        if port != original_port:
            logging.info(f"Port {original_port} was in use or reserved. Using port {port} instead.")

        browser_path = get_browser_executable_path(browser_name)
        if not browser_path:
            return False, port, f"Could not find executable for browser: {browser_name}"

        # Create a temporary user data directory
        user_data_dir = tempfile.mkdtemp(prefix=f"browser-use-{browser_name}-{port}-")
        
        if browser_name == "firefox":
            cmd = [
                browser_path,
                "--remote-debugging-port", str(port),
                "-profile", user_data_dir,
                "-no-remote",
                "-new-instance"
            ]
        else:
            cmd = [
                browser_path,
                f"--remote-debugging-port={port}",
                f"--user-data-dir={user_data_dir}",
                "--no-first-run",
                "--no-default-browser-check"
            ]
            
            # Add common flags for automation
            if browser_name in ["chrome", "chromium"]:
                cmd.extend([
                    "--remote-debugging-address=0.0.0.0",
                    "--password-store=basic",
                    "--use-mock-keychain"
                ])

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        BROWSER_PROCESSES[port] = {
            "process": process,
            "user_data_dir": user_data_dir,
            "browser_name": browser_name
        }

        # Wait a bit for the browser to initialize the CDP port
        time.sleep(2)
        
        logging.info(f"Browser '{browser_name}' started with CDP on port {port}")
        return True, port, None

    except Exception as e:
        logging.error(f"Failed to start browser: {e}")
        return False, port, str(e)


def is_browser_running(port=9999):
    return is_port_in_use(port)


def get_browser_connection(port=9999):
    if not is_browser_running(port):
        return None

    # Prefer 127.0.0.1 for local connections to avoid issues with network IPs and firewalls
    ip = "127.0.0.1"
    
    # Try to get the actual WebSocket URL from the browser
    import httpx
    try:
        response = httpx.get(f"http://{ip}:{port}/json/version", timeout=5.0)
        logging.info(f"Querying http://{ip}:{port}/json/version - Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            logging.info(f"Response data: {data}")
            ws_url = data.get('webSocketDebuggerUrl')
            if ws_url:
                logging.info(f"Found WebSocket URL: {ws_url}")
                return {
                    "ip": ip,
                    "port": port,
                    "cdp_url": ws_url,
                    "ws_endpoint": ws_url
                }
            else:
                logging.warning(f"No webSocketDebuggerUrl in response: {data.keys()}")
        else:
            logging.warning(f"Got status {response.status_code}, response: {response.text[:200]}")
    except Exception as e:
        logging.warning(f"Could not fetch WebSocket URL from /json/version: {e}")
    
    # Fallback to basic WebSocket URL (may not work for all browsers)
    return {
        "ip": ip,
        "port": port,
        "cdp_url": f"ws://{ip}:{port}/",
        "ws_endpoint": f"ws://{ip}:{port}/"
    }


def close_browser(port=9999):
    try:
        if port not in BROWSER_PROCESSES:
            return False, f"No browser process tracked on port {port}"

        browser_info = BROWSER_PROCESSES[port]
        process = browser_info["process"]
        user_data_dir = browser_info["user_data_dir"]

        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
            logging.info(f"Browser on port {port} terminated.")
        else:
            logging.info(f"Browser on port {port} was already stopped.")

        # Clean up the temporary user data directory
        if os.path.exists(user_data_dir):
            # Give it a tiny bit of time to release files if needed
            time.sleep(1)
            shutil.rmtree(user_data_dir, ignore_errors=True)
            logging.info(f"Cleaned up user data directory: {user_data_dir}")

        del BROWSER_PROCESSES[port]
        return True, None

    except Exception as e:
        logging.error(f"Error closing browser: {e}")
        return False, str(e)

