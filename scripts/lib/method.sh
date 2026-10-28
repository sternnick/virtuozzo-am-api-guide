#!/usr/bin/env bash
# method.sh - shared runner for the generated scripts/ tree. Part of tools/gen-scripts.py
# output conventions; keep in the repo (regeneration never overwrites this file).
#
#   method.sh <api-path> "<space-separated required params>" [key=value ...] [--dry-run]
#
# Behaviour:
#   - validates that every required parameter was given (fail before sending, never after);
#   - --dry-run prints the exact request that WOULD go out, with the credential redacted;
#   - the real call is delegated to tools/vz-api.sh, which owns the verb guard: write-class
#     methods stop there unless VZ_ALLOW_DESTRUCTIVE=1. This runner never weakens that guard.
set -euo pipefail
path="${1:?usage: method.sh <api-path> <required> [key=value...] [--dry-run]}"; req="${2:-}"; shift 2 || true

entries=()
for a in "$@"; do
  case "$a" in
    --dry-run) dry=1 ;;
    *=*) entries+=("$a") ;;
    *) echo "method.sh: not a key=value argument: $a" >&2; exit 1 ;;
  esac
done
dry="${dry:-0}"

missing=()
for r in $req; do
  hit=0
  for e in ${entries[@]+"${entries[@]}"}; do
    case "$e" in "$r="*) hit=1; break ;; esac
  done
  [ "$hit" = 1 ] || missing+=("$r")
done

if [ "$dry" = 1 ]; then
  echo "DRY-RUN GET https://${VZ_HOST:-SET-VZ-HOST}/1.0${path}"
  echo "          session=<from VZ_TOKEN, redacted>"
  for e in ${entries[@]+"${entries[@]}"}; do echo "          $e"; done
  if [ "${#missing[@]}" -gt 0 ]; then
    echo "          would FAIL: missing required parameter(s): ${missing[*]}"
  fi
  exit 0
fi

if [ "${#missing[@]}" -gt 0 ]; then
  echo "method.sh: missing required parameter(s): ${missing[*]}" >&2
  echo "  path: $path   (supply them, or run with --dry-run to see the request)" >&2
  exit 1
fi

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
args=()
for e in ${entries[@]+"${entries[@]}"}; do args+=(--param "$e"); done
exec "$root/tools/vz-api.sh" "$path" ${args[@]+"${args[@]}"}
