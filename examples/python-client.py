#!/usr/bin/env python3
"""python-client.py - command line for the stdlib client in vz_client.py.

    export VZ_HOST="app.<your-platform-domain>"
    export VZ_TOKEN="..."
    ./examples/python-client.py /users/account/rest/getuserinfo
    ./examples/python-client.py /environment/control/rest/getenvinfo envName=my-env
    ./examples/python-client.py /environment/control/rest/stopenv envName=my-env    # refuses

Exit codes: 0 success, 1 usage or configuration, 2 refused by the verb guard,
4 the API answered with a non-zero result.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from vz_client import ApiError, Client, Refused  # noqa: E402


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__)
        return 1
    path = argv[1]
    params = dict(p.split("=", 1) for p in argv[2:] if "=" in p)
    try:
        body = Client().call(path, **params)
    except Refused as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 2
    except ApiError as exc:
        print(str(exc), file=sys.stderr)
        return 4
    print(json.dumps(body, indent=1)[:4000])
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
