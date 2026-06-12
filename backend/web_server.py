"""Tiny local HTTP server for playing web (HTML5 / Unity WebGL) game builds.

Unity WebGL refuses to run from file:// and its compressed assets
(.unityweb/.gz/.br) need the right Content-Encoding header or the loader fails.
This serves a single game folder over http://127.0.0.1:<port> with the correct
Content-Type + Content-Encoding so builds load offline.
"""
import os
import mimetypes
import threading
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn

_COMPRESSION_SUFFIXES = (".unityweb", ".gz", ".br")


def _content_type(name):
    low = name.lower()
    for suf in _COMPRESSION_SUFFIXES:
        if low.endswith(suf):
            low = low[: -len(suf)]
            break
    if low.endswith(".wasm"):
        return "application/wasm"
    if low.endswith(".js") or low.endswith(".mjs"):
        return "application/javascript"
    if low.endswith(".json"):
        return "application/json"
    if low.endswith(".data"):
        return "application/octet-stream"
    if low.endswith(".html") or low.endswith(".htm"):
        return "text/html; charset=utf-8"
    if low.endswith(".css"):
        return "text/css; charset=utf-8"
    return mimetypes.guess_type(low)[0] or "application/octet-stream"


def _content_encoding(path):
    """gzip/br for compressed builds. .unityweb is ambiguous → sniff the gzip
    magic (1f 8b); otherwise assume brotli (modern Unity default)."""
    low = path.lower()
    if low.endswith(".gz"):
        return "gzip"
    if low.endswith(".br"):
        return "br"
    if low.endswith(".unityweb"):
        try:
            with open(path, "rb") as f:
                return "gzip" if f.read(2) == b"\x1f\x8b" else "br"
        except Exception:
            return None
    return None


class _ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
    allow_reuse_address = True
    daemon_threads = True


def _make_handler(root):
    root = os.path.abspath(root)

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def _resolve(self):
            rel = urllib.parse.unquote(urllib.parse.urlparse(self.path).path).lstrip("/")
            if not rel:
                rel = "index.html"
            full = os.path.abspath(os.path.join(root, rel))
            # prevent path traversal outside the served folder
            if full != root and not full.startswith(root + os.sep):
                return None
            if os.path.isdir(full):
                full = os.path.join(full, "index.html")
            return full

        def _serve(self, body=True):
            full = self._resolve()
            if not full or not os.path.isfile(full):
                self.send_error(404)
                return
            try:
                size = os.path.getsize(full)
                self.send_response(200)
                self.send_header("Content-Type", _content_type(full))
                enc = _content_encoding(full)
                if enc:
                    self.send_header("Content-Encoding", enc)
                self.send_header("Content-Length", str(size))
                self.send_header("Cache-Control", "no-store")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                if body:
                    with open(full, "rb") as f:
                        while True:
                            chunk = f.read(64 * 1024)
                            if not chunk:
                                break
                            self.wfile.write(chunk)
            except (BrokenPipeError, ConnectionResetError):
                pass
            except Exception:
                try:
                    self.send_error(500)
                except Exception:
                    pass

        def do_GET(self):
            self._serve(body=True)

        def do_HEAD(self):
            self._serve(body=False)

    return Handler


def serve_folder(folder):
    """Start a threaded HTTP server rooted at `folder` on a free local port.
    Returns (httpd, port). Stop with httpd.shutdown()."""
    httpd = _ThreadingHTTPServer(("127.0.0.1", 0), _make_handler(folder))
    port = httpd.server_address[1]
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd, port
