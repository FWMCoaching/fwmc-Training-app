import http.server
import socketserver

PORT = 8845

class Handler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        if self.path.endswith(".html") or self.path == "/":
            self.send_header("Content-Type", "text/html; charset=utf-8")
        elif self.path.endswith(".js"):
            self.send_header("Content-Type", "application/javascript; charset=utf-8")
        elif self.path.endswith(".json"):
            self.send_header("Content-Type", "application/json; charset=utf-8")
        super().end_headers()

class Server(socketserver.ThreadingTCPServer):
    # Plain TCPServer serializes requests (one connection at a time), which
    # becomes the bottleneck once several Playwright/Chromium instances hit
    # it concurrently (see run_full_suite_parallel.sh) - each test's page
    # load/asset fetches would queue up behind every other test's. Threaded
    # handling removes that; allow_reuse_address avoids "Address already in
    # use" on a quick restart (TIME_WAIT from the previous run).
    allow_reuse_address = True
    daemon_threads = True

with Server(("", PORT), Handler) as httpd:
    httpd.serve_forever()
