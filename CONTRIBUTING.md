# Contributing

## What belongs here

Measured behaviour of the Platform API from a **read-only** point of view, expressed so that it is true
for whoever reads it:

- a `result` code we can reproduce, with the request shape that produced it (placeholders only);
- an endpoint that exists or does not exist on a build, with the code that proves it;
- a guardrail that stopped something bad from happening in a script.

What does not belong here: anything that identifies an operator. No real hostnames, no environment
names, no customer names, no balances, no ticket numbers, no IP addresses, no node identifiers. The
publish gate enforces this mechanically, so a leak is a CI failure rather than a maintainer's judgement
call.

## Before you commit

```bash
./tools/check-redaction.py .        # must print "0 finding(s)"
python3 -m compileall -q tools examples
bash -n tools/*.sh
python3 - <<'PY'                    # the ASCII rule, in place of a dependency
import pathlib, sys
bad = []
for p in pathlib.Path('.').rglob('*'):
    if p.is_file() and '.git' not in p.parts:
        t = p.read_text(encoding='utf-8', errors='ignore')
        for cp in ('\u2014', '\u2013', '\u201c', '\u201d', '\u2018', '\u2019'):
            if cp in t:
                bad.append(f"{p}: U+{ord(cp):04X}")
print("\n".join(bad) or "ascii ok")
sys.exit(1 if bad else 0)
PY
```

Dashes and quotes: type `-` and `"`. An em dash in a diff is a character that other people's tools
cannot search for.

## Provenance for a claim

A page should say what was measured and what was inferred. When a statement came from a specific build,
say "on the build tested" and point at the command that checks it, rather than naming a tenant or
publishing a version string that identifies one.

## Safety claims

If you add a method to the destructive list or a guard to a tool, add the reason. A guard that nobody
can justify is the guard that gets deleted the first time it is inconvenient.
