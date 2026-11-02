"""Local web server for the prototype. Run: python app.py, then open http://localhost:8000

Standard library only. Listens on this computer alone (127.0.0.1). All decisions and checks run
on the server; the page only displays them and sends the person's choices.
"""

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from triage.inbox import Inbox

ROOT = Path(__file__).resolve().parent
STATIC = {"/": ("index.html", "text/html"), "/app.js": ("app.js", "text/javascript"),
          "/style.css": ("style.css", "text/css")}
SECURITY_HEADERS = {
    "Content-Security-Policy": "default-src 'self'; script-src 'self'; style-src 'self'; "
                               "img-src 'self'; connect-src 'self'; frame-ancestors 'none'",
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
}
MAX_REQUEST_BYTES = 10_000

inbox = Inbox()
lock = threading.Lock()


def handle_action(path, data):
    """Map each request from the page to one inbox algorithm."""
    global inbox
    actions = {
        "/api/move": lambda: inbox.move(data.get("id"), data.get("section"), data.get("reason")),
        "/api/undo": lambda: inbox.undo_move(data.get("id")),
        "/api/rules/save": lambda: inbox.save_rule(data.get("rule_id")),
        "/api/rules/discard": lambda: inbox.discard_rule(),
        "/api/rules/edit": lambda: inbox.edit_rule(data.get("rule_id"), data.get("section")),
        "/api/rules/renew": lambda: inbox.renew_rule(data.get("rule_id")),
        "/api/rules/forget": lambda: inbox.forget_rule(data.get("rule_id")),
        "/api/request": lambda: inbox.handle_request(str(data.get("text", ""))[:500]),
    }
    if path == "/api/reset":
        inbox = Inbox()
        return {"reset": True}
    if path not in actions:
        return None
    return actions[path]()


class Handler(BaseHTTPRequestHandler):

    def send(self, status, body, content_type="application/json"):
        payload = body if isinstance(body, bytes) else json.dumps(body).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", f"{content_type}; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        for name, value in SECURITY_HEADERS.items():
            self.send_header(name, value)
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self):
        if self.path in STATIC:
            name, kind = STATIC[self.path]
            return self.send(200, (ROOT / "static" / name).read_bytes(), kind)
        if self.path == "/api/inbox":
            with lock:
                return self.send(200, inbox.view())
        self.send(404, {"error": "Not found."})

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        if length > MAX_REQUEST_BYTES:
            return self.send(413, {"error": "Request too large."})
        try:
            data = json.loads(self.rfile.read(length) or b"{}")
            if not isinstance(data, dict):
                raise ValueError
        except ValueError:
            return self.send(400, {"error": "The request could not be read."})
        with lock:
            result = handle_action(self.path, data)
            if result is None:
                return self.send(404, {"error": "Not found."})
            result["inbox"] = inbox.view()
        self.send(400 if "error" in result else 200, result)

    def log_message(self, fmt, *args):
        pass  # keep the console quiet; the page shows every outcome


if __name__ == "__main__":
    server = ThreadingHTTPServer(("127.0.0.1", 8000), Handler)
    print("Email triage prototype running at http://localhost:8000 (Ctrl+C to stop)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()
