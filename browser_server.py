import subprocess
import logging
from utils import get_local_ip, is_port_in_use

logging.basicConfig(
    filename="logs/browser.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

BROWSER_PROCESSES = {}  # port → process object


def start_browser(browser_name="firefox", port=9999):
    try:
        if browser_name not in ["firefox", "webkit", "chrome"]:
            return False, f"Invalid browser: {browser_name}"

        if is_port_in_use(port):
            return False, f"Port {port} already in use"

        cmd = [
            "playwright",
            "run-server",
            f"--browser={browser_name}",
            f"--port={port}"
        ]

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        BROWSER_PROCESSES[port] = process

        logging.info(f"Browser '{browser_name}' started on port {port}")
        return True, None

    except Exception as e:
        logging.error(f"Failed to start browser: {e}")
        return False, str(e)


def is_browser_running(port=9999):
    return is_port_in_use(port)


def get_browser_connection(port=9999):
    if not is_browser_running(port):
        return None

    return {
        "ip": get_local_ip(),
        "port": port,
        "wsEndpoint": f"ws://{get_local_ip()}:{port}/"
    }

def close_browser(port=9999):
    try:
        if port not in BROWSER_PROCESSES:
            return False, f"No browser process tracked on port {port}"

        process = BROWSER_PROCESSES[port]

        if process.poll() is None: 
            process.terminate()
            process.wait(timeout=5)
            logging.info(f"Browser on port {port} terminated.")
        else:
            logging.info(f"Browser on port {port} was already stopped.")

        del BROWSER_PROCESSES[port]
        return True, None

    except Exception as e:
        logging.error(f"Error closing browser: {e}")
        return False, str(e)

