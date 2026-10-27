# 2. The two API surfaces

One hostname serves two different dispatchers. They have different URL shapes, different permission
models and different failure vocabularies. Confusing them is the single most common reason people
conclude "the API is broken" when it is not.

## Surface 1: the Platform REST API

```
https://app.${PLATFORM_DOMAIN}/1.0/<group>/<subgroup>/rest/<method>
```

Examples:

```
/1.0/users/account/rest/getuserinfo
/1.0/environment/control/rest/getenvs
/1.0/environment/control/rest/getenvinfo?envName=${ENV_NAME}
/1.0/billing/account/rest/getquotas
/1.0/users/collaboration/rest/getmembers
/1.0/marketplace/jps/rest/getengineversion
```

This is the surface the vendor documents as the Platform API and the one a personal access token is
usually allowed to use. Notes:

- Method slugs are **lowercase**. `getList` is not `getlist`.
- Verb-first naming is the rule: `get*`, `set*`, `add*`, `remove*`, `start*`, `stop*`, `restart*`,
  `deploy*`, `create*`, `delete*`.
- An unknown slug does not answer JSON. It answers a **bare Apache Tomcat 404 HTML page**. That HTML is
  the signal for "this method does not exist on this build", which is different from `result: 1702`
  (see below) and different from a permission denial.
- Both `GET` and `POST` work in practice even though the vendor OpenAPI spec declares every operation as
  `post`.

## Surface 2: the dashboard ("hx-core") API

The same JSON-RPC-ish dispatcher the web dashboard itself uses:

```
https://app.${PLATFORM_DOMAIN}/api/<service>/<subservice>/<method>
```

The URL path is mapped straight onto a dotted script name: the path `a/b/c` becomes `api.a.b.c`. That is
why the paths look like the permission names in the token editor:

| Token permission shown in the UI | Callable at |
|---|---|
| `env.node.stat` | `/api/env/node/stat` |
| `env.node.redeploy` | `/api/env/node/redeploy` |
| `utils.batch.call` | `/api/utils/batch/call` |
| `system.env.managing.create` | `/api/system/env/managing/create` |

Failure vocabulary:

- `result: 1702`, `"script = api.x.y not found"` - the path is not mapped on this build. No conclusion
  about authentication or permissions is available from this answer.
- `result: 8`, `"Token is not allowed for method: <m>, service: api.<svc>"` - the token authenticated.
  It is not granted this method. This is the answer a REST-only token gives on essentially every
  dashboard method, which is exactly how you learn that a token was minted for the REST surface.
- `result: 702` - invalid or expired token.

## Telling which surface your token owns

`tools/vz-capability-scan.sh` does this systematically. By hand, two requests are enough:

```bash
curl -s -G "https://app.${PLATFORM_DOMAIN}/1.0/users/account/rest/getuserinfo" \
     --data-urlencode "session=${VZ_TOKEN}" | jq '.result'      # 0 => REST works
curl -s -G "https://app.${PLATFORM_DOMAIN}/api/system/user/getinfo" \
     --data-urlencode "session=${VZ_TOKEN}" | jq '.result'      # 0 => dashboard too; 8 => not this token
```

Practical consequences:

- Anything the dashboard shows you that is *not* in the Platform API (a few statistics panels, internal
  settings screens) generally needs a dashboard-surface permission, or needs the browser, or needs SSH
  into the environment.
- A token that is refused on `/api/` is not a broken token. On one build we measured, the same token
  class was permitted across the dashboard surface while a freshly minted one was refused everywhere
  except REST. Whether `/api/` answers depends on the permission sets selected at generation time, not
  on the platform.
- Some methods exist on one surface and not the other. `utils.batch.call`, which batches many calls into
  one request, is a dashboard-surface method; the REST equivalent is absent on the build we tested. If
  you need call batching, check it exists before designing around it.

## Endpoints that are not endpoints

People try these and report them as dead API hosts. They are not the API:

| URL | What it actually is |
|---|---|
| `https://api.${PLATFORM_DOMAIN}/` | an environment-routing edge; answers "no such environment", it is not an API host |
| `https://app.${PLATFORM_DOMAIN}/JElastic/` | dashboard asset path |
| `https://app.${PLATFORM_DOMAIN}/webgate/` | not an API entry point |
| `https://app.${PLATFORM_DOMAIN}/status.jsp` | not served; the dispatcher answers `1702` |
| `https://app.${PLATFORM_DOMAIN}/1.0/utils/batch/call` | not mapped (`1702`) - the batch method lives on the dashboard surface |
