#!/usr/bin/env python3
"""spec-verbs.py - turn the vendor OpenAPI spec into a usable endpoint index.

Usage:
    ./tools/spec-verbs.py                      # histogram of verbs and services
    ./tools/spec-verbs.py --reads              # every read-shaped slug (safe to call)
    ./tools/spec-verbs.py --destructive        # every slug that changes state
    ./tools/spec-verbs.py --grep domain        # filter by substring
    ./tools/spec-verbs.py --spec ./api_8.0.2.json

The spec is fetched from the vendor's public SDK repository unless --spec names a local file, so you
can run this offline. It is a generated artifact from an older API revision: use it as an index and
confirm each slug against your own platform with tools/vz-capability-scan.sh.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.request

DEFAULT_SPEC = (
    "https://raw.githubusercontent.com/CustomScripts/jelastic-api/master/spec/api_8.0.2.json"
)
READ = re.compile(r"(?:^|/)(?:get|check|is|find|list)[a-z0-9]*$")
WRITE = re.compile(
    r"(?:^|/)(?:stop|start|restart|reboot|delete|destroy|remove|add|create|set|edit|apply|deploy"
    r"|bind|unbind|attach|detach|scale|update|install|uninstall|redeploy|reset|rebuild|move|swap"
    r"|register|unregister|enable|disable|clone|migrate|transfer|import|export|run|exec|kill|cancel)"
    r"[a-z0-9]*$"
)


def load(path_or_url: str) -> dict:
    if path_or_url.startswith("http"):
        req = urllib.request.Request(path_or_url, headers={"User-Agent": "spec-verbs"})
        with urllib.request.urlopen(req, timeout=30) as fh:  # nosec - public vendor repo, https
            return json.load(fh)
    with open(path_or_url, encoding="utf-8") as fh:
        return json.load(fh)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", default=DEFAULT_SPEC)
    ap.add_argument("--reads", action="store_true")
    ap.add_argument("--destructive", action="store_true")
    ap.add_argument("--grep", default="")
    args = ap.parse_args()

    try:
        spec = load(args.spec)
    except Exception as exc:  # noqa: BLE001
        print(f"cannot load spec: {exc}", file=sys.stderr)
        return 1

    paths = spec.get("paths", {})
    servers = spec.get("servers") or []
    sec = spec.get("securityDefinitions") or spec.get("components", {}).get("securitySchemes", {})
    print(f"# spec version {spec.get('info', {}).get('version')} | {len(paths)} paths", file=sys.stderr)
    print(f"# servers   {servers}", file=sys.stderr)
    print(f"# auth      {sorted(sec)} in query: "
          f"{[v.get('name') for v in sec.values() if v.get('in') == 'query']}", file=sys.stderr)

    want = []
    if args.reads:
        want = [p for p in sorted(paths) if READ.search(p)]
    elif args.destructive:
        want = [p for p in sorted(paths) if WRITE.search(p) and not READ.search(p)]
    else:
        services: dict[str, int] = {}
        verbs: dict[str, int] = {}
        for p in paths:
            services["/".join(p.split("/")[:3])] = services.get("/".join(p.split("/")[:3]), 0) + 1
            slug = p.rsplit("/", 1)[-1]
            verb = re.match(r"[a-z]+", slug).group(0) if re.match(r"[a-z]+", slug) else "?"
            verbs[verb] = verbs.get(verb, 0) + 1
        print("\n# by service")
        for svc, n in sorted(services.items(), key=lambda kv: -kv[1]):
            print(f"{n:5d}  {svc}")
        print("\n# by verb (first token of the slug)")
        for verb, n in sorted(verbs.items(), key=lambda kv: -kv[1]):
            flag = "  <- state changing" if WRITE.search("/" + verb) else ""
            print(f"{n:5d}  {verb}{flag}")
        print(f"\n# reads {len([p for p in paths if READ.search(p)])}"
              f" | writes {len([p for p in paths if WRITE.search(p) and not READ.search(p)])}")
        want = []

    if args.grep:
        want = [p for p in want if args.grep in p]
    for p in want:
        print(p)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
