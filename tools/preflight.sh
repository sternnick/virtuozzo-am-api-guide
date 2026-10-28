#!/usr/bin/env bash
# preflight.sh - the read-only pre-flight from docs/05, in one command.
#
#   VZ_HOST=app.<your-platform-domain> VZ_TOKEN=*** ./tools/preflight.sh
#
# Runs, in order: identity, environment inventory, in-flight platform actions, engine
# version, server clock. Every call is a get*/read-shaped call via tools/vz-api.sh; this
# script cannot change anything. Exit 0 only if every step answered result 0; exit 4 on the
# first failing step's call having answered at all, 3 on a transport error. Use it before any
# automation touches a platform, and paste its output into change tickets.
set -uo pipefail
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
vz="$root/tools/vz-api.sh"
rc=0

step() {
  local label="$1" path="$2"
  local out code jq_expr="${3:-.result}"
  out="$("$vz" "$path" 2>/dev/null)"; code=$?
  if [ "$code" -ge 3 ]; then
    printf '%-28s TRANSPORT-ERROR %s\n' "$label" "$path"; rc=3; return
  fi
  local summary
  summary="$(printf '%s' "$out" | jq -rc "$jq_expr" 2>/dev/null || echo 'unparseable')"
  if [ "$code" -eq 0 ]; then
    printf '%-28s PASS  %s\n' "$label" "$summary"
  else
    printf '%-28s FAIL  result=%s\n' "$label" "$(printf '%s' "$out" | jq -rc '.result' 2>/dev/null || echo '?')"
    [ "$rc" -lt 4 ] && rc=4
  fi
}

step "identity"          /users/account/rest/getuserinfo      '{uid: .uid, email: .email, authType: .authConfig.type}'
step "environments"      /environment/control/rest/getenvs    '[.infos[].env.envName]'
step "actions in flight" /environment/tracking/rest/getcurrentactions '(.array // []) | length'
step "engine version"    /marketplace/jps/rest/getengineversion      '.version'
step "server clock"      /environment/tracking/rest/getserverutctime '.data // .result'

case "$rc" in
  0) echo 'PREFLIGHT: clean - safe to proceed with read automation' ;;
  4) echo 'PREFLIGHT: at least one step answered non-zero - resolve before automation' ;;
  3) echo 'PREFLIGHT: transport error - check VZ_HOST, egress, and TLS' ;;
esac
exit "$rc"
