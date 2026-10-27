#!/usr/bin/env python3
"""vz_client.py - a minimal, read-only-first client for the V/AM Platform API (stdlib only).

    export VZ_HOST="app.<your-platform-domain>"
    export VZ_TOKEN="..."                      # or VZ_TOKEN_FILE=/path/to/token
    from vz_client import Client
    Client().call("/users/account/rest/getuserinfo")
    Client().call("/environment/control/rest/getenvinfo", envName="my-env")
    Client().call("/environment/control/rest/stopenv", envName="my-env")          # raises Refused
    Client().call("/environment/control/rest/stopenv", envName="my-env", allow_write=True)

The guard is the point of the example: a client that will not send a write verb unless the caller opts
in explicitly is a client that cannot take an environment down by accident. See
docs/05-safety-and-destructive-verbs.md for why `allow_write` exists but must stay opt-in.
"""
from __future__ import annotations

import json
import os
import re
import ssl
import sys
import urllib.error
import urllib.parse
import urllib.request

__all__ = ["ApiError", "Client", "Refused"]

READ = re.compile(r"(?:^|/)(?:get|check|is|find|list)[a-z0-9]*$")
WRITE = re.compile(
    r"(?:^|/)(?:stop|start|restart|reboot|delete|destroy|remove|add|create|set|edit|apply|deploy"
    r"|bind|unbind|attach|detach|scale|update|install|uninstall|redeploy|reset|rebuild|move|swap"
    r"|register|unregister|enable|disable|clone|migrate|transfer|import|export|run|exec|kill|cancel)"
    r"[a-z0-9]*$"
)
CODES = {0: "ok", 2: "method refuses token auth", 3: "parameter required", 7: "session expired",
         8: "token out of scope on this surface", 11: "environment not found",
         702: "token invalid or expired", 705: "no rights on that object",
         1702: "path not mapped on this build", 2303: "environment not created"}


class ApiError(RuntimeError):
    """A response whose `result` field is not 0. HTTP status is not the signal here."""

    def __init__(self, result: int, source: str, error: str) -> None:
        super().__init__(f"result {result} [{source}] {error} ({CODES.get(result, 'undecoded')})")
        self.result, self.source, self.error = result, source, error


class Refused(RuntimeError):
    """Raised by the verb guard before any request leaves the process."""


class Client:
    def __init__(self, host: str | None = None, token: str | None = None,
                 timeout: float = 30.0, verify: bool = True) -> None:
        host = host or os.environ.get("VZ_HOST")
        if not host:
            raise SystemExit("set VZ_HOST, e.g. app.<your-platform-domain> (no scheme)")
        if not token:
            path = os.environ.get("VZ_TOKEN_FILE")
            if path:
                with open(path, encoding="utf-8") as fh:
                    token = fh.read().strip()
            token = token or os.environ.get("VZ_TOKEN")
        if not token:
            raise SystemExit("set VZ_TOKEN or VZ_TOKEN_FILE")
        self.host, self.token, self.timeout = host, token, timeout
        self.ctx = ssl.create_default_context()
        if not verify:                                  # self-hosted edges behind an internal CA
            self.ctx.check_hostname = False
            self.ctx.verify_mode = ssl.CERT_NONE

    def call(self, path: str, allow_write: bool = False, **params: object) -> dict:
        slug = path.rstrip("/").rsplit("/", 1)[-1]
        if not READ.search(slug):
            if not allow_write:
                raise Refused(
                    f"{path} is not a get*/check*/is*/find*/list* method. Re-call with "
                    "allow_write=True after reading docs/05-safety-and-destructive-verbs.md."
                )
            print(f"WARNING: state-changing call {path} {sorted(params)}", file=sys.stderr)
        query = urllib.parse.urlencode({"session": self.token, **params})
        url = f"https://{self.host}/1.0{path}?{query}"
        try:
            with urllib.request.urlopen(url, timeout=self.timeout, context=self.ctx) as resp:
                raw = resp.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                raise ApiError(404, "http", "REST slug not mapped on this build") from exc
            raise
        body = json.loads(raw)
        if body.get("result", 0) != 0:
            raise ApiError(body.get("result"), body.get("source", "-"), body.get("error", ""))
        return body


# Command-line use: see examples/python-client.py, which imports this module.
