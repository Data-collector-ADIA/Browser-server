# Browser Server

A Python project to manage **remote Playwright browsers** (Firefox, Chrome, WebKit) and expose them via IP + port for remote connections.  
This allows distributed systems, RPC servers, or backends to control browsers remotely.

---

## Features

- Start a browser in **remote server mode** on a specific port.
- Check if the browser server is running.
- Get connection information (IP, port, WebSocket endpoint).
- Stop/close the browser safely.
- Works with **Playwright 1.40+**.
- Supports Firefox, Chrome, and WebKit.

