# Virtuozzo Application Management: API field notes

Field notes on programmatically driving a **Virtuozzo Application Management** (V/AM) platform - the
Virtuozzo distribution of the Jelastic PaaS control plane - with a **personal access token**.

This is what a real, read-only reconnaissance pass against a live platform produced: which HTTP surface
answers, where the token has to go, what each error code actually means, how to find the endpoint list
when your token is not allowed to ask for it, and which calls you must never put in a script.

No tenant-specific data lives here. Every example uses `${PLATFORM_DOMAIN}`, `${TOKEN}` and
`${ENV_NAME}` placeholders, and `tools/check-redaction.py` fails the build on any hostname that is not
on its allow list. Read [SECURITY.md](SECURITY.md) before you paste a token anywhere.

## Unofficial

Not affiliated with, endorsed by, or sponsored by Virtuozzo or Jelastic. Virtuozzo and Jelastic are
trademarks of their owners. The vendor docs are the source of truth; this repository records the
measured behaviour behind them. Test on a staging or trial account before you automate a platform that
hosts anything you care about.

## The short version

1. There are **two HTTP surfaces on the same host**, and a token may be permitted on one and refused on
   the other:

   | Surface | Shape | Typical fate for a personal access token |
   |---|---|---|
   | Platform REST API | `https://app.${PLATFORM_DOMAIN}/1.0/<group>/<sub>/rest/<method>` | works, usually broadly |
   | Dashboard ("hx-core") API | `https://app.${PLATFORM_DOMAIN}/api/<svc>/<sub>/<method>` | often refused with `result: 8`, depending on which permission sets were ticked |

2. The token goes in the **`session` query parameter**. Nothing else works:

   ```bash
   curl -s -G "https://app.${PLATFORM_DOMAIN}/1.0/users/account/rest/getuserinfo" \
        --data-urlencode "session=${TOKEN}"
   ```

   `Cookie: session=...`, `Authorization: Bearer ...` and `Authorization: Basic ...` are all ignored and
   the request is handled as unauthenticated. The parameter may also be sent in a POST form body.

3. **HTTP status is 200 even on failure.** The control signal is the `result` field of the JSON body.
   See [docs/03-error-codes.md](docs/03-error-codes.md).

4. You cannot ask a token what it is allowed to do. The self-inspection methods
   (`users/authentication/rest/gettokens`, `gettokenapilist`, `getsessions`) answer `result: 2`
   "Method call via token is forbidden". Read the permission list from the dashboard UI, or reconstruct
   it with the OpenAPI catalogue described in [docs/04-discovering-endpoints.md](docs/04-discovering-endpoints.md).

5. Control verbs exist and act. `stopenv`, `startenv`, `deleteenv`, `restartnodes`,
   `restartnodebyid`, `restartcontainerbyid` are ordinary REST slugs on the same base path as the read
   methods. Treat them as the `rm -rf` of this API: see
   [docs/05-safety-and-destructive-verbs.md](docs/05-safety-and-destructive-verbs.md).

## Quick start

```bash
export VZ_HOST="app.${PLATFORM_DOMAIN}"     # your platform hostname, no scheme
export VZ_TOKEN="..."                        # Settings -> Access Tokens -> Generate
./tools/vz-api.sh /users/account/rest/getuserinfo         # who am I
./tools/vz-api.sh /environment/control/rest/getenvs       # what exists
./tools/vz-capability-scan.sh > capability.tsv            # what this token can actually reach
./scripts/environment/control/getenvinfo.sh envName=...   # generated per-method wrapper
./scripts/environment/control/stopenv.sh envName=...       # refuses, and explains why
```

Every tool is `curl` plus `jq` plus bash. No SDK install, no vendor PHP client, no API key in a
config file: the token is read from `VZ_TOKEN` and never written to disk.

## Contents

| Path | What it answers |
|---|---|
| [docs/01-authentication.md](docs/01-authentication.md) | sessions vs personal access tokens, scopes, 2FA, what to avoid |
| [docs/02-two-api-surfaces.md](docs/02-two-api-surfaces.md) | `/1.0/...` vs `/api/...`, how to tell which one your token owns |
| [docs/03-error-codes.md](docs/03-error-codes.md) | the `result` codes, decoded, with what to do about each |
| [docs/04-discovering-endpoints.md](docs/04-discovering-endpoints.md) | getting a method catalogue when the API will not give you one |
| [docs/05-safety-and-destructive-verbs.md](docs/05-safety-and-destructive-verbs.md) | the auth-order trap, destructive verbs, guarding a fleet you did not build |
| [docs/06-recipes.md](docs/06-recipes.md) | copy-paste read-only recipes: identity, inventory, billing, nodes, ACLs |
| [tools/vz-api.sh](tools/vz-api.sh) | the safe client: query encoding, result decoding, verb guard |
| [tools/vz-capability-scan.sh](tools/vz-capability-scan.sh) | classify every read-only method for one token |
| [tools/spec-verbs.py](tools/spec-verbs.py) | extract the endpoint catalogue and its verb histogram from the vendor OpenAPI spec |
| [tools/gen-scripts.py](tools/gen-scripts.py) | generate (or CI-verify) one wrapper per Platform API method |
| [scripts/](scripts/README.md) | the generated suite: every documented method callable as `scripts/<group>/<sub>/<slug>.sh key=value` |
| [docs/07-the-script-suite.md](docs/07-the-script-suite.md) | how the generated wrappers guard, dry-run, and stay consistent |
| [tools/check-redaction.py](tools/check-redaction.py) | publish gate: refuse to commit a hostname or a token-shaped string |
| [examples/python-client.py](examples/python-client.py) | a ~60-line Python client with the same guard |
| [examples/env-inventory.py](examples/env-inventory.py) | flatten `getenvs` into a small, shareable inventory (JSON or TSV) |

## Verifying on your own platform

Three commands establish the whole picture without changing anything:

```bash
# 1. which surface does my token own?
curl -s -G "https://app.${PLATFORM_DOMAIN}/1.0/users/account/rest/getuserinfo" \
     --data-urlencode "session=${TOKEN}" | head -c 200

curl -s -G "https://app.${PLATFORM_DOMAIN}/api/env/node/stat" \
     --data-urlencode "session=${TOKEN}" | head -c 200

# 2. is the token alive? (result 702 = dead or revoked, result 8 = alive but out of scope)
# 3. what build is this? (never assume; the endpoint catalogue depends on it)
curl -s -G "https://app.${PLATFORM_DOMAIN}/1.0/marketplace/jps/rest/getengineversion" \
     --data-urlencode "session=${TOKEN}"
```

## Licence

MIT. See [LICENSE](LICENSE).

Everything here is generic on purpose. If you are reading this because you found a hostname in a URL and
expected it to appear in these pages, it will not: the publish gate rejects it.
