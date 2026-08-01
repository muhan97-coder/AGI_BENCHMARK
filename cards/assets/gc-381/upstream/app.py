# gc-381 SEALED slow origin. Do not modify this file.
# Serves /api/item/<n> with an artificial 200ms delay, short cache TTL (max-age=30),
# and counts origin hits. /__count reports the total (never cache it).
import json
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

COUNT = {"n": 0}


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/__count":
            body = json.dumps({"upstream_requests": COUNT["n"]}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Cache-Control", "no-store")
        elif self.path.startswith("/api/item/"):
            COUNT["n"] += 1
            time.sleep(0.2)
            item = self.path.rsplit("/", 1)[-1]
            body = json.dumps({"item": item, "origin": "slow-origin"}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Cache-Control", "public, max-age=30")
        else:
            body = b"not found"
            self.send_response(404)
            self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    HTTPServer(("0.0.0.0", 9000), Handler).serve_forever()
