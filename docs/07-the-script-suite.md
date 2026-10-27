# 7. The generated script suite

`scripts/` holds one executable per Platform API method - every method the vendor currently
documents, callable by path, generated from the live OpenAPI catalogue described in
[04-discovering-endpoints.md](04-discovering-endpoints.md) (Source 0). It exists so that platform
testing is `./scripts/<group>/<sub>/<slug>.sh key=value`, never hand-written curl under time
pressure.

## What is in the tree

| Artifact | Content |
|---|---|
| `scripts/index.tsv` | every method: `path`, `class` (read/write), required parameters |
| `scripts/<group>/<sub>/<slug>.sh` | one wrapper per method (422 at spec 8.15) |
| `scripts/lib/method.sh` | the shared runner (not for direct use) |
| `data/api-catalog.json` | the derived catalogue: paths, classes, parameter names - no descriptions |
| `tools/gen-scripts.py` | the generator; `--check` verifies the tree against the committed catalogue, offline |

## How a wrapper behaves

```bash
VZ_HOST=app.<your-platform-domain> VZ_TOKEN=*** \
  ./scripts/environment/control/getenvinfo.sh envName=my-env
```

- Required parameters are checked **before anything leaves the process**. A missing one is a
  local exit 1, not a `result: 3` round trip.
- `--dry-run` prints the exact request (URL, parameters, credential redacted) and exits 0,
  including a `would FAIL: missing required parameter(s): ...` line when arguments are incomplete.
- The real call delegates to `tools/vz-api.sh`, so the verb guard lives in exactly one place and
  exit codes are the ones documented in [03-error-codes.md](03-error-codes.md).

## Classification is fail-closed

A wrapper labelled `read` is exactly a `get*/check*/is*/find*/list*` slug - the same vocabulary
the client guard uses. That means readlog- or search-shaped slugs (`readlog`, `searchactions`,
`actions`, `loadalerthistory`) are labelled `write` and need the override. The asymmetry is the
point: a wrong `read` label could take an environment down; a wrong `write` label costs one
environment variable.

The spec lists `session` (and sometimes `appid`/`checksum`) inside some operations' form bodies.
Those are injected by the client and excluded from each wrapper's required-check - you should
never pass `session=` by hand.

## Regenerating

```bash
python3 tools/gen-scripts.py            # fetches the live vendor spec (browser UA; CloudFront trap)
python3 tools/gen-scripts.py --spec f   # from a local copy of the spec
python3 tools/gen-scripts.py --check    # offline consistency check (what CI runs)
```

The generator refuses to emit anything unless every path and parameter name it saw matches
`^[A-Za-z][A-Za-z0-9_]*$`. Raw spec prose never enters the tree, which is what keeps the
redaction gate in `.github/workflows/validate.yml` meaningful - the vendor's descriptions contain
dotted strings that would otherwise read as hostnames.

## Testing against a platform, when credentials arrive

1. Run the pre-flight from [05-safety-and-destructive-verbs.md](05-safety-and-destructive-verbs.md)
   (identity, envs, in-flight actions, engine version).
2. `./tools/vz-capability-scan.sh --from-catalog` classifies every read-shaped script against
   your token.
3. Anything the scan marks `callable` is proven; `param-needed` (result 3) tells you which
   required parameter the catalogue could not infer. Keep write-class execution for a staging
   account, with the `--dry-run` output reviewed before dropping the flag.
