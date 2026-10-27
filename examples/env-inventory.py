#!/usr/bin/env python3
"""env-inventory.py - flatten /environment/control/rest/getenvs into a small, auditable inventory.

    ./examples/env-inventory.py > inventory.json
    ./examples/env-inventory.py --tsv

Deliberately field-limited: it emits names, domains, node roles, sizes and engine versions, and nothing
that resembles a credential or a customer identifier. That makes the output safe to paste into a ticket
or commit to an internal repository, which the raw API response is not.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from vz_client import ApiError, Client  # noqa: E402


def fetch() -> list[dict]:
    return Client().call("/environment/control/rest/getenvs").get("infos", [])


def flatten(infos: list[dict]) -> list[dict]:
    rows = []
    for group in infos:
        env = group.get("env") or {}
        for node in group.get("nodes") or []:
            custom = node.get("customitem") or {}
            rows.append({
                "envName": env.get("envName"),
                "domain": env.get("domain"),
                "displayName": env.get("displayName"),
                "status": env.get("status"),
                "hostGroup": env.get("hostGroup"),
                "node": node.get("name"),
                "nodeGroup": node.get("nodeGroup"),
                "nodeType": node.get("nodeType"),
                "engineType": node.get("engineType"),
                "engineVersion": custom.get("engineVersion"),
                "os": custom.get("dockerOs") or node.get("guestOSType"),
                "cpu": node.get("cpu"),
                "ram": node.get("ram"),
                "hdd": node.get("hdd"),
                "fixedCloudlets": node.get("fixedCloudlets"),
                "flexibleCloudlets": node.get("flexibleCloudlets"),
            })
    return rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tsv", action="store_true", help="tab-separated instead of JSON")
    args = ap.parse_args()
    try:
        rows = flatten(fetch())
    except ApiError as exc:
        print(str(exc), file=sys.stderr)
        return 4
    if not rows:
        print("no environments visible to this token", file=sys.stderr)
        return 4
    if args.tsv:
        cols = list(rows[0])
        print("\t".join(cols))
        for r in rows:
            print("\t".join("" if r[c] is None else str(r[c]) for c in cols))
    else:
        json.dump({"environments": sorted({r["envName"] for r in rows if r["envName"]}),
                   "nodes": rows}, sys.stdout, indent=1)
        print()
    print(f"# {len({r['envName'] for r in rows if r['envName']})} environments, "
          f"{len(rows)} nodes", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
