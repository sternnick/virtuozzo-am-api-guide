# 3. The `result` field, decoded

Transport status is **200 for practically everything**. Write your error handling against the `result`
field of the JSON body, never against `curl -f` or `response.ok`. The one exception is an unmapped REST
slug, which answers an HTTP 404 with an Apache Tomcat HTML page instead of JSON.

| `result` | Meaning | What to do |
|---|---|---|
| `0` | success | read the payload; often alongside `data`, `infos`, `array`, `objects` or `envGroups` |
| `2` | "Method call via token is forbidden" | the method refuses token auth by design (session and token management). Use the dashboard UI |
| `3` | missing or invalid parameter | the path exists **and** you are authorised; add the named parameter. The error names it: `invalid parameter [nodeGroup] for method [Get] in service [NodegroupService]` |
| `7` | session expired / not authorised (session auth) | re-authenticate, or switch to a token |
| `8` | "Token is not allowed for method" | token is valid; grant the method in Settings -> Access Tokens, or use the other surface |
| `11` | "Can't find environment by domain" | wrong name, or an environment your user cannot see. Not a token verdict |
| `2303` | environment for that appid not created | usually a stale or half-deleted environment |
| `702` | "Token is invalid or expired" | re-issue the token. This is the only code that says the credential is dead |
| `705` | "user [uid] doesn't have any access rights to app [id]" | per-environment ACL. Account-wide calls work while per-environment calls fail. Not a token bug |
| `1702` | "script = api.x.y not found" | the URL is not mapped on this build. Wrong path, wrong surface, or a method this version does not have. No auth conclusion |
| HTTP 404 + Tomcat HTML | REST slug absent from this build | compare with the vendor OpenAPI spec and your platform's version |

A response also carries `source`, which names the dispatcher that answered and is the fastest way to see
which surface served you:

| `source` | came from |
|---|---|
| `"hx-core"` | the dashboard dispatcher (including the `1702` mapping failures you get under `/1.0/`) |
| `"JEL"` | the platform core, i.e. a real REST method ran |
| `"BILL"` | the billing subsystem (answers under `billing/account/rest/...`) |

So a `/1.0/...` call that answers `source: "hx-core"` with `1702` never reached the platform API at all:
the path fell through to the dashboard dispatcher. That is how you distinguish "wrong REST slug" from
"REST method answered and refused me".

## Why `3` is good news

`result: 3` is the most useful failure in this API: it proves the path is mapped, proves the credential
was accepted far enough to validate its arguments, and tells you the exact parameter name to add. The
capability scan classifies an endpoint as "callable, parameter required" on the strength of a `3`.

## A decoding helper

```bash
decode() {                       # url... -> compact verdict
  curl -s -G "$1" --data-urlencode "session=${VZ_TOKEN}" \
  | jq -c '{r: .result, src: .source, e: (.error // "")}'
}
```

`tools/vz-api.sh` implements the same mapping and exits non-zero on any non-zero `result`, so it can be
used in a pipeline:

```bash
./tools/vz-api.sh /environment/control/rest/getenvs | jq '.infos[].env.envName'
```
