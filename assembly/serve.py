"""Serve the viewer on 127.0.0.1:8772 with caching off, so a rebuild always shows up on refresh.

    python serve.py
"""
import functools
import http.server
import os


class NoCache(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-store, must-revalidate")
        self.send_header("Expires", "0")
        super().end_headers()


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    handler = functools.partial(NoCache, directory=here)
    http.server.ThreadingHTTPServer(("127.0.0.1", 8772), handler).serve_forever()
