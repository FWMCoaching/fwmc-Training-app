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

with socketserver.TCPServer(("", PORT), Handler) as httpd:
    httpd.serve_forever()
