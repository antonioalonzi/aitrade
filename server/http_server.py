import threading
import logging

from http.server import HTTPServer, BaseHTTPRequestHandler

logger = logging.getLogger("HttpServer")

class HttpServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <body style="background: #111; color: #00ff00; font-family: monospace; padding: 50px;">
            <h1>Matrix Server Core</h1>
            <p>Web server status: RUNNING</p>
        </body>
        </html>
        """
        self.wfile.write(bytes(html_content, "utf-8"))

def run_server():
    server = HTTPServer(("localhost", 8080), HttpServer)
    logger.info("Server is running at http://localhost:8080")
    server.serve_forever()
