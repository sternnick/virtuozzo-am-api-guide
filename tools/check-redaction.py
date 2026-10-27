#!/usr/bin/env python3
"""check-redaction.py - the publish gate for this repository.

Two questions, both answered without containing any secret itself:

1. Is every hostname in the tree either a public documentation/vendor domain on the allow list, or an
   explicit placeholder? An allow list is used deliberately: a deny list would have to *contain* the
   tenants, customers and internal hosts it is meant to protect, which is the leak it prevents.
2. Does any file contain a credential-shaped string (long hex/base64/base32 runs) that looks like it
   could be a real session or personal access token?

Placeholders that are fine: ${PLATFORM_DOMAIN}, ${ENV_NAME}, app.<your-platform-domain>,
[hoster-api-host], example.com, localhost.

Exit codes: 0 clean, 1 findings, 2 the scan examined nothing (a vacuous pass is not a pass).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path

ALLOW = {
    # the products this repository documents
    "virtuozzo.com", "jelastic.com",
    # where this repository and its references live
    "github.com", "raw.githubusercontent.com", "api.github.com",
    "objects.githubusercontent.com", "codeload.github.com", "gist.githubusercontent.com",
    # documentation stand-ins and loopback
    "example.com", "example.org", "localhost", "127.0.0.1", "::1",
}
ALLOW_SUFFIXES = (".example", ".invalid", ".local", ".test")

# A candidate is only treated as a hostname when its last label is a real registry suffix. Without
# this, `os.environ`, `json.load`, `utils.batch.call` and `README.md` all look like hosts and the gate
# drowns in noise - which is how a gate like this gets switched off.
TLD_SUFFIX = {
    "com", "net", "org", "io", "dev", "app", "cloud", "tech", "xyz", "info", "biz", "co", "me",
    "ai", "sh", "gg", "eu", "uk", "de", "fr", "nl", "be", "es", "it", "pt", "gr", "cy", "ie", "ch",
    "at", "se", "no", "dk", "fi", "pl", "cz", "hu", "ro", "bg", "hr", "si", "sk", "lt", "lv", "ee",
    "is", "ua", "tr", "ru", "il", "ae", "sa", "za", "ng", "ke", "ma", "eg", "br", "mx", "ar", "cl",
    "ca", "us", "au", "nz", "jp", "kr", "cn", "in", "sg", "hk", "tw", "th", "my", "id", "vn", "ph",
}
# ... and not when it is a filename we are all writing.
FILE_SUFFIX = {
    "md", "rst", "py", "pyc", "sh", "bash", "zsh", "fish", "js", "ts", "jsx", "json", "jsonc",
    "toml", "yaml", "yml", "ini", "cfg", "conf", "env", "lock", "sum", "mod", "txt", "log", "csv",
    "tsv", "sql", "xml", "html", "htm", "css", "scss", "jsp", "php", "rb", "go", "rs", "java", "c",
    "h", "cpp", "hcl", "tf", "tpl", "svg", "png", "jpg", "jpeg", "gif", "webp", "pdf", "gz", "tgz",
    "zip", "tar", "deb", "rpm", "whl", "gem", "jar", "woff", "woff2", "ttf", "exe", "bin", "bak",
    "orig", "rej", "diff", "patch", "min", "map", "old", "tmp", "sample", "example",
}

HOST = re.compile(
    r"(?<![\w.$-])((?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+"
    r"[a-z]{2,24})(?![\w.-])"
)
IPV4 = re.compile(r"(?<![\d.])(?:\d{1,3}\.){3}\d{1,3}(?![\d.])")
PLACEHOLDER_HINT = re.compile(r"[<>]|\$\{|\$\(|envName=<|hoster-api-host")
SECRETISH = [
    (re.compile(r"\b[0-9a-fA-F]{32,}\b"), "long hex run (token-shaped)"),
    (re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"), "GitHub token"),
    (re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b"), "GitHub fine-grained token"),
    (re.compile(r"(?i)\b(bearer\s+)[A-Za-z0-9._-]{24,}"), "bearer value"),
    (re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"), "private key"),
    (re.compile(r"(?i)(password|passwd|secret|api[_-]?key)\s*[=:]\s*['\"]?[^\s'\"$<][^\s'\"$<]{7,}"),
     "assignment of a secret-looking value"),
    (re.compile(r"session=(?!\$|\{|<)[A-Za-z0-9]{20,}"), "literal session value"),
]
BINARY_OK = {".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".woff", ".woff2"}
SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv"}

# Non-ASCII policy for a repository that intends to be read anywhere.
BANNED_CHARS = {
    "\u2014": "em dash", "\u2013": "en dash",
    "\u201c": "left double quote", "\u201d": "right double quote",
    "\u2018": "left single quote", "\u2019": "right single quote",
    "\u2026": "horizontal ellipsis", "\u00a0": "non-breaking space",
}
BANNED_RANGES = ((0x4E00, 0x9FFF), (0x3040, 0x30FF), (0xAC00, 0xD7AF),
                 (0x3000, 0x303F), (0xFF00, 0xFF60))


def in_banned_range(cp: int) -> bool:
    return any(lo <= cp <= hi for lo, hi in BANNED_RANGES)


def walk(root: Path) -> list[Path]:
    out = []
    for p in sorted(root.rglob("*")):
        if p.is_dir() or any(part in SKIP_DIRS for part in p.parts):
            continue
        out.append(p)
    return out


def registrable(host: str) -> str:
    return host


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("root", nargs="?", default=".")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    if not root.is_dir():
        print(f"not a directory: {root}", file=sys.stderr)
        return 2
    files = [f for f in walk(root) if f.suffix.lower() not in BINARY_OK]
    if not files:
        print("vacuous scan: no files examined", file=sys.stderr)
        return 2

    findings: list[dict] = []
    for f in files:
        try:
            text = f.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            findings.append({"file": str(f), "line": 0, "kind": "undecodable file",
                             "detail": "cannot audit binary or mixed encoding"})
            continue
        rel = f.relative_to(root)
        for lineno, line in enumerate(text.splitlines(), 1):
            for m in IPV4.finditer(line):
                ip = m.group(0)
                if ip not in {"127.0.0.1", "0.0.0.0"}:
                    findings.append({"file": str(rel), "line": lineno, "kind": "raw IP address",
                                     "detail": f"{ip}  |  {line.strip()[:80]}"})
            for m in HOST.finditer(line):
                host = m.group(1).lower()
                tld = host.rsplit(".", 1)[-1]
                if tld in FILE_SUFFIX or tld not in TLD_SUFFIX:
                    continue                       # a filename or an attribute, not a host
                base = host
                if base in ALLOW or base.endswith(ALLOW_SUFFIXES):
                    continue
                if any(base.endswith("." + a) for a in ALLOW):
                    continue
                # a hostname inside a placeholder construct is a placeholder
                ctx = line[max(0, m.start() - 12): m.end() + 12]
                if PLACEHOLDER_HINT.search(ctx) or "$" in ctx or "<" in ctx or "{" in ctx:
                    continue
                findings.append({"file": str(rel), "line": lineno,
                                  "kind": "hostname not on the allow list",
                                  "detail": f"{host}  |  {line.strip()[:100]}"})
            for rx, label in SECRETISH:
                for m in rx.finditer(line):
                    findings.append({"file": str(rel), "line": lineno, "kind": label,
                                     "detail": m.group(0)[:24] + "..."})
            for col, ch in enumerate(line, 1):
                if ch in BANNED_CHARS:
                    findings.append({"file": str(rel), "line": lineno,
                                     "kind": f"non-ASCII: {BANNED_CHARS[ch]}",
                                     "detail": f"U+{ord(ch):04X} at column {col}"})
                elif ord(ch) > 127 and (in_banned_range(ord(ch)) or any(
                        unicodedata.category(ch).startswith(c) for c in ("Cf", "Co"))):
                    findings.append({"file": str(rel), "line": lineno, "kind": "non-ASCII",
                                     "detail": f"U+{ord(ch):04X} at column {col}"})

    if args.json:
        print(json.dumps(findings, indent=1))
    else:
        for fnd in findings:
            print(f"{fnd['file']}:{fnd['line']}: {fnd['kind']}: {fnd['detail']}")
        print(f"scanned {len(files)} files, {len(findings)} finding(s)")
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
