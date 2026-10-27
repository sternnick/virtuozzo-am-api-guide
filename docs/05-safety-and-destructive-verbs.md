# 5. Safety, destructive verbs, and one auth-order trap

A PaaS control-plane API is a fleet-wide mutation interface with a JSON body. The same token that lists
your environments can stop one of them. This page is the part that keeps a reconnaissance pass from
becoming an incident.

## The trap: authorization can be evaluated after the object is resolved

On the build tested for these notes, this request:

```
GET /1.0/environment/control/rest/stopenv?envName=<some-real-environment>&session=<a-garbage-token>
```

does **not** fail authentication. It resolves the environment first. With a nonexistent name it returns
`result: 11` "Can't find environment by domain" *even when the credential is garbage*, and with a real
name the call proceeds far enough to be alarming. Two consequences:

1. **Never use a control method as a liveness or permission probe.** It proves nothing about the token
   and it risks acting on a real object.
2. **Environment existence is enumerable by anyone who can reach the endpoint with any non-empty
   `session` string.** Treat that as an information-disclosure finding for your own build: verify it
   read-only (nonexistent names only, garbage credential, no real `envName`), and if it reproduces,
   report it to your hosting provider or the vendor through
   [SECURITY.md](../SECURITY.md) rather than as an issue on this repository.

The read-only recipes in these notes never send a real environment name to a state-changing verb, and
neither should your scripts.

## The verbs to be afraid of

They are ordinary slugs on the same base path as the read methods, which is why a copy-paste from an API
reference page is dangerous. Extract the current list mechanically:

```bash
./tools/spec-verbs.py --destructive
```

From the vendor spec that includes at least:

```
/environment/control/rest/stopenv
/environment/control/rest/startenv
/environment/control/rest/deleteenv
/environment/control/rest/restartnodes
/environment/control/rest/restartnodebyid
/environment/control/rest/restartcontainerbyid
/environment/control/rest/restartservices
```

plus every `create*`, `remove*`, `add*`, `set*`, `bind*`, `deploy*`, `destroy*`, `edit*` and
`apply*` sibling. On one tested build, `/environment/control/rest/stopenv` and `startenv` were live
while several other control slugs were absent, so you cannot assume a verb is missing just because a
tutorial says so.

Guardrails that work:

- **Name the target explicitly.** Never let `envName` come from a variable that can be empty. An empty
  `envName` resolves against a default context and produces `result: 705` referencing an app you did not
  name - which is how you know the call was about to do something.
- **Fail closed on ambiguity.** If a script cannot print the exact environment it is about to touch and
  get a yes, it should not run.
- **Separate read and write clients.** `tools/vz-api.sh` and `examples/python-client.py` here refuse any
  non-read slug unless you pass an explicit override.
- **Do not batch control verbs.** `utils.batch.call` is a dashboard-surface method and does not exist on
  the REST surface of the build tested; do not invent a REST equivalent.

## Operational manners

- One request in flight. This is a control plane shared with other tenants and with your own running
  applications; a 30-request scan is fine, a loop over `getstats` for every node every second is not.
- Long-running platform work is asynchronous. Check `environment/tracking/rest/getcurrentactions` rather
  than polling a mutating call, and read `getaction` for progress on a specific action id.
- Statistics endpoints are per-node and per-interval. Pulling them at a high rate is the fastest way to
  make a shared platform dislike your integration.
- `3` responses are cheap, `0` responses on read methods are cheap, `2` responses are free. Use them as
  your probe vocabulary.

## Pre-flight checklist before any automation touches a platform

1. `getuserinfo` - which identity is this token, and is it the account you meant?
2. `getenvs` - how many environments exist, and would you be upset if one stopped?
3. `getcurrentactions` - is someone else already changing the platform right now?
4. Version check (`marketplace/jps/rest/getengineversion`) - does the endpoint catalogue you wrote the
   code against match this build?
5. A dry-run mode in your own code that prints the exact URL path and object name without calling it.
