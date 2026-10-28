# 4. Discovering the endpoint catalogue

There is a chicken-and-egg problem: to know what a token may call you would like to ask the platform,
but the methods that answer that question refuse token authentication.

```
/1.0/users/authentication/rest/gettokens        -> result 2, "Method call via token is forbidden"
/1.0/users/authentication/rest/gettokenapilist  -> result 2
/1.0/users/authentication/rest/getsessions      -> result 2
/api/system/settings/getapilist                 -> result 8 (dashboard surface, not granted)
```

So the catalogue has to come from somewhere else. Four sources, best first.

## Source 0: the vendor's live OpenAPI spec (the authoritative one)

The vendor publishes a machine-readable catalogue of the current Platform API next to the API docs
themselves:

```
https://docs.jelastic.com/api/resources/api.json
```

Measured properties of this file (fetched 2026-10-27, spec `info.version` **8.15**, page footer
"API v. 8.15.1"):

| Property | Value |
|---|---|
| Format | OpenAPI 3.0 (`openapi: "3.0.0"`) |
| Operations | **422**, every one declared `post` |
| Server | `https://{host}/1.0/` (matches Surface 1 exactly) |
| Security scheme | `components.securitySchemes.SessionAuth` = apiKey, `in: query`, `name: session` |
| Parameters | per-operation `requestBody` with `application/x-www-form-urlencoded` schemas and `required` lists |
| `appid`/`checksum` | per-request parameter mentions (428 / 3 occurrences), **not** top-level schemes |

Fetching it has one trap: CloudFront in front of `www.virtuozzo.com` answers **403 to a bare
`Mozilla/5.0` User-Agent** and 200 to a full browser UA. The same applies to the docs site itself:
`https://docs.jelastic.com/` redirects to `www.virtuozzo.com/application-platform-docs/` and is 403 to
scripted clients without the header, while `docs.jelastic.com/api/` (the spec and the generated doc
pages) answers 200 without it:

```bash
curl -sL -A 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36' \
     -o vendor-api.json https://docs.jelastic.com/api/resources/api.json
```

Measured distribution of the 422 operations (service = first two path segments):

| Service | Ops | Service | Ops |
|---|---|---|---|
| `environment.control` | 91 | `iaas.volume` | 11 |
| `users.collaboration` | 32 | `environment.build` | 11 |
| `environment.binder` | 28 | `marketplace` app | 10 |
| `environment.file` | 23 | `iaas.lb` | 10 |
| `environment.deployment` | 21 | `users.team` | 9 |
| `iaas.vm` | 18 | `environment.security` | 9 |
| `environment.trigger` | 18 | *(`marketplace` x5, `iaas` x11, others)* | ~140 |
| `billing.subscription` | 15 | | |
| `users.authentication` | 12 | | |

Verb-shape split of the same 422: **128** match the conservative read pattern
(`get*/check*/is*/find*/list*`), **230** match a state-changing verb, and **64** match neither
(`signin`, `upload`, `rename`, `searchactions`, `readlog`, `buildproject`, `restoredump`,
`activatemember`, ...). Treat that last bucket as state-changing unless you have proven otherwise:
`searchactions` and `readlog` are reads, `upload` and `writelog` are absolutely not.

The raw file is **not safe to vendor into a redaction-checked repository**: its descriptions contain
Java package strings rooted in the vendor's legacy hivext namespace (tails like `.dev` and `.com` make
them look like hostnames to a gate) and ccTLD-shaped tokens inside parameter prose (a quota name ending
in the two-letter country code for Greece, for example, trips a naive hostname regex). Extract the
catalogue (paths, required parameters, verb classes) instead - `tools/gen-scripts.py` does exactly that
and keeps the raw spec out of the tree.

## Source 1: the generated PHP SDK's spec (older revision)

[`CustomScripts/jelastic-api`](https://github.com/CustomScripts/jelastic-api) is a generated PHP SDK for
the Platform API. Its `spec/api_8.0.2.json` is the interesting file, and it is the same surface these
notes describe:

```json
"servers": [{ "url": "https://[hoster-api-host]/1.0/" }],
"securityDefinitions": {
  "SessionAuth":  { "type": "apiKey", "in": "query", "name": "session"  },
  "AppidAuth":    { "type": "apiKey", "in": "query", "name": "appid"    },
  "ChecksumAuth": { "type": "apiKey", "in": "query", "name": "checksum" }
}
```

Same base path, same `session`-in-query rule. That is the confirmation that the URL pattern in these
notes is the documented one and not an accident of one platform.

What it gives you: **310 operations** (measured 2026-10-27 against `spec/api_8.0.2.json`), distributed
like this:

| Path prefix | Operations | What lives there |
|---|---|---|
| `/environment/control` | ~91 | environments, nodes, containers, logs, statistics |
| `/users/collaboration` | ~31 | members, roles, policies, resource ACLs |
| `/environment/binder` | ~26 | domains, SSL certificates, external IPs |
| `/environment/file` | ~23 | cloud files, mounts, favourites |
| `/environment/deployment` | ~21 | build/deploy projects, hooks, repositories |
| `/environment/trigger` | ~18 | autoscaling and load-alert triggers |
| `/users/authentication` | ~12 | login, sessions, tokens (all token-forbidden) |
| `/environment/build` | ~11 | VCS build projects |
| `/marketplace/*` | ~33 | catalogues, installations, settings, JPS |
| others | ~50 | billing, scheduler, security rules, groups, export, tracking, vcs |

`tools/spec-verbs.py` parses it and prints the verb histogram plus every destructive slug, which is what
you want before you let anything script against a real platform.

Treat the spec as an **index, not an oracle**:

- It is a one-off generated drop (a single "Initial commit", last pushed in 2023, no licence file, no
  maintenance). Nobody is updating it.
- It describes an older API revision than a current platform. Expect two kinds of drift: slugs the spec
  lists that this build answers `404` or `1702` for, and slugs the build has that the spec never saw.
- Every operation is declared `post`. `get` works too, which matters when you write a client that only
  issues GET for read-only safety.

Verify a slug with exactly one request, and read the answer through
[the error table](03-error-codes.md): `3` means it exists, `0` means it exists and is callable right
now, `705` means it exists but you lack rights on that object, `1702`/HTML-`404` means this build does
not have it.

## Source 2: your own platform, with read-only calls

If you would rather not depend on a third-party repository, enumerate the read-only shapes you already
know and classify the answers. `tools/vz-capability-scan.sh` does exactly that over a built-in list of
`get*` / `check*` / `is*` / `find*` methods and prints a matrix:

| verdict | from |
|---|---|
| `callable` | `result: 0` |
| `param-needed` | `result: 3` (exists, add the named argument) |
| `needs-env` | `result: 705` or `2303` (exists, needs an object you can name) |
| `forbidden-by-token` | `result: 2` |
| `absent` | `1702` or an HTML 404 |

Two rules while scanning: only call `get*`-shaped methods, and never send a real environment name to a
verb that changes state.

## Source 3: the dashboard's own traffic

The browser client calls the dashboard surface, so its requests *are* the catalogue for that surface.
Open the dashboard with dev tools, click around, and read the `/api/...` paths; each one is a
permission-able method name, and the dotted form is what the Access Token editor lists. This is the only
way to discover dashboard-surface methods that no public spec documents.

The same trick works on the static bundle: the dashboard JavaScript contains the dotted script names it
calls, so `grep -o` over the shipped `.js` recovers method names without clicking through the UI. Mind
your provider's terms before automating a browser session against a managed control plane.

## Reconstructing the permission set of a token

Because the API will not tell you, the honest procedure is:

1. Scan the read-only catalogue with the token. Everything that answers `0`, `3`, `705` or `2303` is
   inside its scope.
2. Everything that answers `2` is a method that refuses token auth regardless of scope - not evidence
   about the token.
3. Everything that answers `8` on the dashboard surface is out of scope.
4. Never test a write verb to find out. The permission model for writes is the same list, so a read-only
   scan plus the Access Tokens screen is sufficient, and it is the only procedure safe to run against a
   platform you do not own outright.
