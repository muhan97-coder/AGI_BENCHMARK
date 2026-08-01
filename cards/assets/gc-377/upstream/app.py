# gc-377 SEALED slow upstream. Do not modify this file.
# Serves /api/item/<n> with an artificial 250ms delay and counts upstream hits.
# /__count reports how many /api/item requests actually reached this origin.
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
            time.sleep(0.25)
            item = self.path.rsplit("/", 1)[-1]
            body = json.dumps({"item": item, "origin": "slow-upstream"}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Cache-Control", "public, max-age=120")
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
