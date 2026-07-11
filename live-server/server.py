#!/usr/bin/env python3
"""
The Long Game · Live Room relay — Python edition, standard library only.

Identical job and wire protocol to server.js, for machines where Node.js isn't
available but Python is (very common on corporate laptops). Serves the game
HTML files AND the realtime room API from one port; nothing external.

    python3 live-server/server.py                 # http://localhost:8877/
    PORT=9000 python3 live-server/server.py       # custom port
    STATIC_DIR=/path/to/html python3 ...          # game files elsewhere

Any .html it serves has its LIVE_BACKEND line rewritten to "auto" on the fly,
so the game file on disk can stay exactly as shipped.

API contract (same as the Firebase RTDB transport / server.js):
    GET  /rooms/CODE[/sub/path].json                  -> JSON value at path
    PUT  /rooms/CODE[/sub/path].json  {body}          -> set value at path
    GET  /rooms/CODE.json (Accept: text/event-stream) -> SSE: "put" {path,data}
         full snapshot on connect, then one event per write; ":ka" every 25s.

State is in-memory and throwaway; rooms idle for ROOM_TTL_MS are purged.
Put the company reverse proxy in front for HTTPS (SSE needs buffering off).
"""
import json
import os
import queue
import re
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORT = int(os.environ.get("PORT", "8877"))
STATIC_DIR = os.path.realpath(os.environ.get("STATIC_DIR",
             os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")))
ROOM_TTL_MS = int(os.environ.get("ROOM_TTL_MS", str(6 * 3600 * 1000)))
MAX_ROOMS, MAX_BODY, MAX_DEPTH = 500, 64 * 1024, 8
KEEPALIVE_S = 25

MIME = {".html": "text/html; charset=utf-8", ".js": "text/javascript", ".css": "text/css",
        ".png": "image/png", ".svg": "image/svg+xml", ".ico": "image/x-icon", ".json": "application/json"}
CORS = [("Access-Control-Allow-Origin", "*"), ("Access-Control-Allow-Methods", "GET,PUT,OPTIONS"),
        ("Access-Control-Allow-Headers", "Content-Type"), ("Cache-Control", "no-store")]

_rooms, _lock = {}, threading.Lock()          # code -> {data, clients:set[Queue], touched}


def room(code):
    with _lock:
        if code not in _rooms:
            if len(_rooms) >= MAX_ROOMS:
                return None
            _rooms[code] = {"data": None, "clients": set(), "touched": time.time()}
        r = _rooms[code]
        r["touched"] = time.time()
        return r


def gc_loop():
    while True:
        time.sleep(1800)
        cutoff = time.time() - ROOM_TTL_MS / 1000
        with _lock:
            for code in [c for c, r in _rooms.items() if r["touched"] < cutoff]:
                for q in _rooms[code]["clients"]:
                    q.put(None)               # tells the SSE thread to close
                del _rooms[code]


def parse_api(path):
    clean = path.split("?")[0]
    clean = clean[:-5] if clean.endswith(".json") else clean
    parts = [p for p in clean.split("/") if p]
    if not parts or parts[0] != "rooms" or len(parts) < 2:
        return None
    if not re.fullmatch(r"[A-Za-z0-9]{1,8}", parts[1]) or len(parts) > MAX_DEPTH:
        return None
    return parts[1].upper(), parts[2:]


def get_at(data, sub):
    node = data
    for k in sub:
        if not isinstance(node, dict) or k not in node:
            return None
        node = node[k]
    return node


def set_at(r, sub, value):
    if not sub:
        r["data"] = value if isinstance(value, dict) else None
        return
    if not isinstance(r["data"], dict):
        r["data"] = {}
    node = r["data"]
    for k in sub[:-1]:
        if not isinstance(node.get(k), dict):
            node[k] = {}
        node = node[k]
    if value is None:
        node.pop(sub[-1], None)
    else:
        node[sub[-1]] = value


def sse_payload(sub, value):
    path = "/" + "/".join(sub) if sub else "/"
    return ("event: put\ndata: " + json.dumps({"path": path, "data": value}) + "\n\n").encode()


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *a):                 # quiet
        pass

    def _headers(self, code, ctype=None, extra=(), length=None, chunkless=False):
        self.send_response(code)
        for k, v in CORS:
            self.send_header(k, v)
        if ctype:
            self.send_header("Content-Type", ctype)
        for k, v in extra:
            self.send_header(k, v)
        if length is not None:
            self.send_header("Content-Length", str(length))
        elif not chunkless:
            self.send_header("Content-Length", "0")
        self.end_headers()

    def _json(self, obj, code=200):
        body = json.dumps(obj).encode()
        self._headers(code, "application/json", length=len(body))
        self.wfile.write(body)

    def do_OPTIONS(self):
        self._headers(204, extra=[("Access-Control-Max-Age", "86400")])

    def do_GET(self):
        api = parse_api(self.path)
        if api is None:
            return self._static()
        code, sub = api
        r = room(code)
        if r is None:
            return self._json({"error": "room limit"}, 503)
        if "text/event-stream" in (self.headers.get("Accept") or ""):
            return self._sse(r)
        with _lock:
            val = get_at(r["data"], sub)
        self._json(val)

    def do_PUT(self):
        api = parse_api(self.path)
        if api is None:
            return self._json({"error": "not found"}, 404)
        code, sub = api
        r = room(code)
        if r is None:
            return self._json({"error": "room limit"}, 503)
        n = int(self.headers.get("Content-Length") or 0)
        if n > MAX_BODY:
            return self._json({"error": "too large"}, 413)
        try:
            value = json.loads(self.rfile.read(n) or b"null")
        except ValueError:
            return self._json({"error": "bad json"}, 400)
        with _lock:
            set_at(r, sub, value)
            clients = list(r["clients"])
        payload = sse_payload(sub, value)
        for q in clients:
            q.put(payload)
        self._json(value)

    def _sse(self, r):
        self._headers(200, "text/event-stream", extra=[("Connection", "keep-alive")], chunkless=True)
        q = queue.Queue()
        with _lock:
            q.put(sse_payload([], r["data"]))
            r["clients"].add(q)
        try:
            while True:
                try:
                    item = q.get(timeout=KEEPALIVE_S)
                except queue.Empty:
                    item = b":ka\n\n"
                if item is None:               # room purged
                    break
                self.wfile.write(item)
                self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError, OSError):
            pass
        finally:
            with _lock:
                r["clients"].discard(q)

    def _static(self):
        p = self.path.split("?")[0]
        if p in ("", "/"):
            p = "/long-term-game-live.html"
        fpath = os.path.realpath(os.path.join(STATIC_DIR, p.lstrip("/")))
        if not fpath.startswith(STATIC_DIR):                      # no traversal
            return self._headers(403)
        if not os.path.isfile(fpath) and p == "/long-term-game-live.html":
            fpath = os.path.join(STATIC_DIR, "index.html")        # graceful default
        if not os.path.isfile(fpath):
            return self._headers(204 if "favicon" in p else 404)
        with open(fpath, "rb") as fh:
            data = fh.read()
        ext = os.path.splitext(fpath)[1].lower()
        if ext == ".html":
            # Same on-the-fly switch as server.js: any served page talks to us.
            data = re.sub(rb'(const LIVE_BACKEND\s*=\s*\{\s*databaseURL:\s*)"[^"]*"',
                          rb'\1"auto"', data)
        self._headers(200, MIME.get(ext, "application/octet-stream"), length=len(data))
        self.wfile.write(data)


def main():
    threading.Thread(target=gc_loop, daemon=True).start()
    srv = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    srv.daemon_threads = True
    print(f"Long Game live relay (Python) on http://localhost:{PORT}/  (static: {STATIC_DIR})", flush=True)
    print('Served pages are auto-switched to LIVE_BACKEND "auto".', flush=True)
    srv.serve_forever()


if __name__ == "__main__":
    main()
