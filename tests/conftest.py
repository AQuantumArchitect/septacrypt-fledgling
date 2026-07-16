import json
import threading
import urllib.request

import pytest

from septacrypt_fledgling.server.app import make_server


class Client:
    """Minimal urllib JSON client against a live in-process server."""

    def __init__(self, port: int):
        self.base = f"http://127.0.0.1:{port}"

    def request(self, method: str, path: str, body=None):
        data = None if body is None else json.dumps(body).encode()
        req = urllib.request.Request(self.base + path, data=data, method=method)
        if data is not None:
            req.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(req) as resp:
                return resp.status, json.loads(resp.read())
        except urllib.error.HTTPError as err:
            return err.code, json.loads(err.read())

    def get(self, path):
        return self.request("GET", path)

    def post(self, path, body=None):
        return self.request("POST", path, body or {})

    def delete(self, path):
        return self.request("DELETE", path)


@pytest.fixture(scope="module")
def client():
    server = make_server(port=0, debug=True)  # debug: schema-validate every payload
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield Client(port)
    server.shutdown()
