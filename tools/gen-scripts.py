#!/usr/bin/env python3
"""gen-scripts.py - generate one callable script per Platform API method.

    ./tools/gen-scripts.py                 # fetch the live vendor spec, regenerate scripts/
    ./tools/gen-scripts.py --spec FILE     # generate from a local copy of the OpenAPI spec
    ./tools/gen-scripts.py --check         # verify scripts/ matches data/api-catalog.json (offline)

Produces:
    data/api-catalog.json   derived catalogue: paths, verb class, parameter names only.
                            Never the raw spec: its prose contains dotted strings that a hostname
                            redaction gate flags, so only ^[A-Za-z0-9_]+$ identifiers are kept.
    scripts/index.tsv       path, class, required-parameter list, one line per method.
    scripts/<group>/<sub>/<slug>.sh   one executable per method (422 at spec 8.15).
    scripts/lib/method.sh   the shared runner all generated scripts exec.

Every generated script delegates to tools/vz-api.sh, so the verb guard stays in exactly one
place: read-shaped slugs run freely, everything else is refused unless VZ_ALLOW_DESTRUCTIVE=1
or --force. Classification here matches that guard's read vocabulary
(get*/check*/is*/find*/list*) - a readlog-shaped slug is therefore labelled write and needs the
override; that is deliberate fail-closed behaviour, see docs/07-the-script-suite.md.
The `session`/`appid`/`checksum` parameters the spec lists on some operations are injected by
the client and excluded from each script's required-argument check.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.request
from pathlib import Path

LIVE_SPEC = "https://docs.jelastic.com/api/resources/api.json"
# CloudFront in front of the vendor docs answers 403 to a bare "Mozilla/5.0" UA.
UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124 Safari/537.36")
READ = re.compile(r"(?:^|/)(?:get|check|is|find|list)[a-z0-9]*$")
IDENT = re.compile(r"^[A-Za-z][A-Za-z0-9_]*$")
CLIENT_PARAMS = {"session", "appid", "checksum"}
ROOT = Path(__file__).resolve().parent.parent

SCRIPT_TMPL = """#!/usr/bin/env bash
# Virtuozzo Application Management Platform API method wrapper (generated).
# path:     {path}
# class:    {cls}
# spec:     {version} (tools/gen-scripts.py - do not edit; regenerate instead)
# required: {required}
# optional: {optional}
#
# Usage:  VZ_HOST=app.<platform> VZ_TOKEN=*** \\
#           {rel} {example} [--dry-run]
# --dry-run prints the exact request without sending it.
# Write-class methods are refused by tools/vz-api.sh unless VZ_ALLOW_DESTRUCTIVE=1.
set -euo pipefail
exec "$(cd "$(dirname "${{BASH_SOURCE[0]}}")/../../.." && pwd)"/scripts/lib/method.sh \\
  {path} "{required_spaced}" "$@"
"""


def load_spec(source: str) -> dict:
    if source.startswith("http"):
        req = urllib.request.Request(source, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=60) as fh:  # nosec - public vendor docs, https
            return json.load(fh)
    with open(source, encoding="utf-8") as fh:
        return json.load(fh)


def catalog_of(spec: dict) -> list[dict]:
    ops = []
    for path in sorted(spec.get("paths", {})):
        op = next(iter(spec["paths"][path].values()), {})
        parts = path.strip("/").split("/")
        if len(parts) != 4 or parts[2] != "rest" or not all(IDENT.match(p) for p in parts):
            sys.exit(f"unexpected path shape, refusing to generate: {path}")
        schema = {}
        for body in (op.get("requestBody", {}).get("content", {}) or {}).values():
            schema = body.get("schema", {}) or schema
        props = list((schema.get("properties") or {}).keys())
        required = [r for r in (schema.get("required") or []) if r not in CLIENT_PARAMS]
        if not all(IDENT.match(p) for p in props + required):
            sys.exit(f"unexpected parameter name, refusing to generate: {path}")
        for cp in CLIENT_PARAMS & set(props):
            required = [r for r in required if r != cp]
        ops.append({"path": path, "group": parts[0], "sub": parts[1], "slug": parts[3],
                    "class": "read" if READ.search("/" + parts[3]) else "write",
                    "required": required, "params": props})
    return ops


def script_body(op: dict, version: str) -> str:
    req = op["required"]
    opt = [p for p in op["params"] if p not in req and p not in CLIENT_PARAMS]
    example = " ".join(f"{r}=<value>" for r in req) or "..."
    return SCRIPT_TMPL.format(
        path=op["path"], cls=op["class"], version=version,
        rel=f"scripts/{op['group']}/{op['sub']}/{op['slug']}.sh",
        required=", ".join(req) or "-", optional=", ".join(opt) or "-",
        required_spaced=" ".join(req), example=example,
    )


def generate(spec_source: str) -> int:
    spec = load_spec(spec_source)
    version = str(spec.get("info", {}).get("version", "?"))
    ops = catalog_of(spec)
    data = {"spec_version": version, "source": spec_source if not spec_source.startswith("http")
            else "docs.jelastic.com (live OpenAPI document)", "operations": ops}
    (ROOT / "data").mkdir(exist_ok=True)
    (ROOT / "data" / "api-catalog.json").write_text(
        json.dumps(data, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    (ROOT / "scripts" / "lib").mkdir(parents=True, exist_ok=True)
    (ROOT / "scripts" / "index.tsv").write_text(
        "".join(f"{o['path']}\t{o['class']}\t{','.join(o['required']) or '-'}\n" for o in ops),
        encoding="utf-8")
    for op in ops:
        p = ROOT / "scripts" / op["group"] / op["sub"] / f"{op['slug']}.sh"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(script_body(op, version), encoding="utf-8")
        p.chmod(0o755)
    reads = sum(1 for o in ops if o["class"] == "read")
    print(f"generated {len(ops)} scripts ({reads} read / {len(ops) - reads} write) "
          f"for spec {version}")
    return 0


def check() -> int:
    cat_path = ROOT / "data" / "api-catalog.json"
    if not cat_path.is_file():
        print("data/api-catalog.json missing - run tools/gen-scripts.py first", file=sys.stderr)
        return 1
    ops = json.loads(cat_path.read_text(encoding="utf-8"))["operations"]
    bad = 0
    for op in ops:
        p = ROOT / "scripts" / op["group"] / op["sub"] / f"{op['slug']}.sh"
        if not p.is_file():
            print(f"missing script: {p}", file=sys.stderr)
            bad += 1
            continue
        if f"# path:     {op['path']}\n" not in p.read_text(encoding="utf-8"):
            print(f"script header path mismatch: {p}", file=sys.stderr)
            bad += 1
    known = {str((ROOT / "scripts" / o["group"] / o["sub"] / f"{o['slug']}.sh").relative_to(ROOT))
             for o in ops}
    for p in (ROOT / "scripts").rglob("*.sh"):
        rel = str(p.relative_to(ROOT))
        if rel.startswith("scripts/lib/") and p.name == "method.sh":
            continue
        if rel not in known:
            print(f"script not in catalog: {rel}", file=sys.stderr)
            bad += 1
    print(f"check: {len(ops)} catalog entries, {0 if bad else 'all scripts present and consistent'}")
    return 1 if bad else 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", default=LIVE_SPEC,
                    help="OpenAPI spec: file path or URL (default: the live vendor document)")
    ap.add_argument("--check", action="store_true", help="verify scripts/ against data/api-catalog.json")
    args = ap.parse_args()
    return check() if args.check else generate(args.spec)


if __name__ == "__main__":
    raise SystemExit(main())
