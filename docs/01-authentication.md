# 1. Authentication

The platform offers two ways to authenticate an API request. They are not interchangeable.

## A. Session-based (the default)

You `POST` credentials, receive a short-lived session identifier, and pass that identifier as the
`session` parameter. On a platform with two-factor authentication enabled (`authConfig.type: "TFA"`)
the login flow needs the second factor as well, which no unattended script can supply. Sessions also
expire, so a long-running job has to log in again and handle the race where a call lands after expiry.

Use it for: interactive tooling, one-off debugging, anything that already has a human in front of a
browser.

## B. Personal access tokens (the automation path)

Tokens are created in the dashboard under **Settings -> Access Tokens**. Each token carries:

- a description, so you can tell yours from a colleague's in an audit trail;
- an optional expiry date (`Expires At`, `dd-mm-yyyy`);
- an **API permission set**: a predefined bundle (Extended Access, IDE Plugins, Marketplace, Maven
  Plugin) or a Custom selection of individual methods.

The dashboard lists these methods by their dotted internal name (`env.node.stat`,
`utils.batch.call`, `system.env.managing.create`). That naming is the same one the dashboard surface
uses in its URL: a scope named `a.b.c` is reachable at `/api/a/b/c`. See
[02-two-api-surfaces.md](02-two-api-surfaces.md).

Notes that cost time to learn:

- The token value is shown **once**. Generate, download, done. Losing it does not lose access; you
  regenerate, which invalidates the old value and breaks every script still using it.
- Every token change needs your password, including regeneration.
- A token can be narrower than your account, but it can never be broader: authorisation is still
  evaluated against your user's rights on each environment. A call can fail with `result: 705` on one
  environment and succeed on the next one with the same token.
- On an account with 2FA enabled, tokens are the documented way to keep automation working without
  shipping a second factor inside the script.

## Where the token goes

Only here:

```
https://app.${PLATFORM_DOMAIN}/1.0/environment/control/rest/getenvs?session=${TOKEN}
```

or in the body of a `POST` (`-d "session=${TOKEN}"`). Verified behaviour of the transports people try
next, all of which are **silently ignored** - the server does not reject them, it answers as if no
credential was supplied:

| Attempt | Result |
|---|---|
| `?session=${TOKEN}` | authenticated |
| POST body `session=${TOKEN}` | authenticated |
| `Cookie: session=${TOKEN}` | treated as anonymous |
| `Authorization: Bearer ${TOKEN}` | treated as anonymous |
| `Authorization: Basic ${TOKEN}:` | treated as anonymous |

There is a second, app-level authentication pair described in the vendor OpenAPI spec - `appid` plus
`checksum` - intended for integrations that sign a request rather than carry a user credential. It is
out of scope for these notes; the token path above is the one that works from a shell.

## Hygiene

```bash
# good: the value lives in the process environment for the life of the shell
export VZ_TOKEN="$(pbpaste)"          # or read from a secret manager
printf '%s\n' "$VZ_TOKEN" | tr -d '\n' > /dev/null   # touch it, do not echo it

# bad, in this order
curl "https://.../1.0/...?session=0123..."      # now it is in your shell history
echo $VZ_TOKEN                                  # now it is in your logs
```

- Because the credential travels in a **query string**, it can land in access logs, proxy logs and
  browser history. Use `-G --data-urlencode` so you never hand-build a URL containing it, and prefer a
  dedicated low-privilege token for anything that runs unattended.
- `curl -G --data-urlencode "session=$VZ_TOKEN"` also avoids the quoting bugs that appear when a token
  is concatenated into a URL inside a script.
- A `403`/`401` from an intermediary (WAF, edge) is not a token problem. Re-run with
  `-o /dev/null -w '%{http_code}'` and look at the transport status separately from `result`.

## Is my token still valid?

Hit **one** dashboard-surface method and read the code:

```bash
curl -s -G "https://app.${PLATFORM_DOMAIN}/api/env/node/stat" \
     --data-urlencode "session=${VZ_TOKEN}" | jq '{result, error}'
```

- `result: 702` - invalid, expired or revoked. Re-issue.
- `result: 8` - **valid**, simply not granted this method. Do not conclude the token is dead.
- `result: 1702` - wrong URL, no authentication conclusion available.

Never use an environment lookup or a control method as a liveness probe. Environment resolution happens
before the session is rejected, so an invalid credential can still return "environment not found" - and,
worse, a control method that resolves an environment may act on it.
See [05-safety-and-destructive-verbs.md](05-safety-and-destructive-verbs.md).
