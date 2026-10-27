# Security

## The credential is the whole account

A personal access token for a hosting control plane is not an API key for one service. It can list
every environment on the account, read configuration and logs inside them, and - if the permission set
allows it - start, stop, redeploy or delete them. Handle it like an SSH key with no passphrase.

Rules this repository follows and asks you to follow:

- Never commit a token. Not in an example, not in a fixture, not in a "cleaned up" log excerpt.
- Keep it in `VZ_TOKEN` or a file only you can read (`chmod 600`), never in a tracked config file, a
  CI log line, or a shell history file you might later paste.
- Pass it with URL encoding (`curl -G --data-urlencode "session=$VZ_TOKEN"`), so it cannot be
  concatenated into a command that later ends up in a log.
- Because the API takes the credential in a **query string**, assume it can appear in reverse-proxy and
  access logs. Generate a dedicated, least-privileged, expiring token per automation task; the dashboard
  supports expiry and per-method scoping precisely for this.
- Revoke by regenerating. Regeneration invalidates the previous value, so plan the redeploy of whatever
  was using it.
- Do not point this repository's tools at a platform you are not authorised to probe. The read-only
  calls still hit someone's control plane.

## What `tools/check-redaction.py` protects

Documentation about a managed platform is easy to write in a way that leaks the operator: real
hostnames, environment names, customer names, node identifiers, balances, ticket numbers, IP addresses.
The publish gate in `tools/` therefore fails on:

- any hostname that is not on its explicit allow list (vendor and public documentation domains);
- raw IP addresses;
- credential-shaped strings (long hex runs, `*_token` shapes, private-key blocks, literal `session=`
  values);
- non-ASCII punctuation that makes text unreadable in other people's terminals and diffs.

It uses an **allow list** on purpose. A deny list would have to contain the very names it protects.

Run it before publishing anything derived from a live platform:

```bash
./tools/check-redaction.py .
```

## Observed behaviour that you should check on your own platform

While working read-only, we observed that a control endpoint resolves the requested environment before
it rejects an invalid `session` value: with a garbage credential and a nonexistent name it answers
"environment not found" rather than an authentication error. Two things follow, and they are
operational advice for your build, not a claim about any particular vendor release:

1. Do not use state-changing endpoints to test credentials, on any platform. It is unsound in general
   and unsafe here specifically.
2. Environment-name existence may be enumerable by an unauthenticated-but-well-formed request. If that
   reproduces on your deployment, it is an information-disclosure issue worth reporting to your hosting
   provider or the vendor, not something to open as a public issue on this repository.

To verify safely on your own platform: use a deliberately invalid credential, use only names that
cannot exist, and never send a real environment name to a `stop`/`start`/`delete` endpoint.

## Disclosing a problem with these tools

Open a private vulnerability report through GitHub's "Report a vulnerability" form for this repository,
or contact the maintainers by any means that does not put the detail in a public thread. Include the
endpoint, the request shape with the credential redacted, and the observed `result` code.
