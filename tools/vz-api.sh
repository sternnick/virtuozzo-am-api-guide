#!/usr/bin/env bash
# vz-api.sh - read-only-first client for the Virtuozzo Application Management Platform API.
#
#   VZ_HOST=app.<your-platform-domain> VZ_TOKEN=... ./tools/vz-api.sh /environment/control/rest/getenvs
#   ./tools/vz-api.sh /environment/control/rest/getenvinfo --param envName=my-env
#   ./tools/vz-api.sh /environment/control/rest/stopenv --param envName=my-env    # refuses
#
# The token is read from VZ_TOKEN (or VZ_TOKEN_FILE) and never written to disk.
# Exit codes: 0 result==0, 1 usage, 2 refused by the verb guard, 3 transport error,
# 4 the API answered with a non-zero result.
set -euo pipefail

host="${VZ_HOST:?set VZ_HOST, e.g. app.<your-platform-domain> (no scheme)}"
if [ -n "${VZ_TOKEN:-}" ]; then
  token="$VZ_TOKEN"
elif [ -n "${VZ_TOKEN_FILE:-}" ] && [ -r "${VZ_TOKEN_FILE}" ]; then
  token="$(tr -d '[:space:]' < "${VZ_TOKEN_FILE}")"
else
  echo "set VZ_TOKEN or VZ_TOKEN_FILE" >&2; exit 1
fi

path="${1:-}"; shift || true
[ -n "$path" ] || { sed -n '2,12p' "$0" >&2; exit 1; }
case "$path" in /*) : ;; *) path="/$path" ;; esac
[ "${path:0:1}" = "/" ] || path="/$path"

params=()
pretty=()
while [ $# -gt 0 ]; do
  case "$1" in
    --param) params+=(--data-urlencode "$2"); pretty+=(--param "$2"); shift 2 ;;
    --force) force=1; shift ;;
    *) echo "unknown argument: $1" >&2; exit 1 ;;
  esac
done

# --- verb guard -------------------------------------------------------------
# Anything that is not clearly a read verb needs an explicit override. The list is
# deliberately over-broad: a false refusal costs one flag, a false acceptance costs an outage.
read_re='(^|/)(get|check|is|find|list)[a-z0-9]*$'
write_re='(^|/)(stop|start|restart|reboot|delete|destroy|remove|add|create|set|edit|apply|deploy|bind|unbind|attach|detach|scale|update|install|uninstall|redeploy|reset|rebuild|move|swap|register|unregister|enable|disable|clone|migrate|transfer|import|export|run|exec|kill|cancel)([a-z0-9]*)$'
slug="${path##*/}"
force="${force:-0}"; [ "${VZ_ALLOW_DESTRUCTIVE:-0}" = "1" ] && force=1

if ! printf '%s' "$slug" | grep -Eq "$read_re"; then
  reason="not a get*/check*/is*/find*/list* slug"
  printf '%s' "$slug" | grep -Eq "$write_re" && reason="state-changing verb"
  if [ "$force" != "1" ]; then
    cat >&2 <<EOF
REFUSED: ${path} (${reason})

This client only issues read calls by default. If you really mean it:
    VZ_ALLOW_DESTRUCTIVE=1 ./tools/vz-api.sh ${path} ${pretty[*]:-}
or, for a one-off:
    ./tools/vz-api.sh ${path} ${pretty[*]:-} --force

Before you do, read docs/05-safety-and-destructive-verbs.md. In particular, do not use a
control verb to test whether a token works: the environment is resolved before the
session is, so such a call can act on a real object instead of failing authentication.
EOF
    exit 2
  fi
  echo "WARNING: state-changing call issued against ${path}" >&2
fi

# --- call -------------------------------------------------------------------
args=(--silent --show-error --max-time 30 -G "https://${host}/1.0${path}"
      --data-urlencode "session=${token}" -w '\n%{http_code}')
for p in ${params[@]+"${params[@]}"}; do args+=("$p"); done
resp="$(curl "${args[@]}" 2>/dev/null)" || { echo "transport error: ${host}${path}" >&2; exit 3; }

body="$(printf '%s' "$resp" | sed '$d')"
http="$(printf '%s' "$resp" | tail -1)"

if [ "$http" = "404" ] || printf '%s' "$body" | grep -qi 'Apache Tomcat'; then
  echo "http 404: this REST slug is not mapped on this build" >&2; exit 4
fi
if ! command -v jq >/dev/null 2>&1; then printf '%s\n' "$body"; exit 0; fi

result="$(printf '%s' "$body" | jq -r '.result // "?"' 2>/dev/null || echo '?')"
[ "$result" = "0" ] || printf '%s' "$body" | jq -r '"result \(.result) [\(.source // "-")] \(.error // "")"' >&2 || true
printf '%s\n' "$body"
[ "$result" = "0" ] || exit 4
