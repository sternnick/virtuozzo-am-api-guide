#!/usr/bin/env bash
# vz-capability-scan.sh - classify which read-only endpoints a given token can reach.
#
#   VZ_HOST=app.<your-platform-domain> VZ_TOKEN=... ./tools/vz-capability-scan.sh > capability.tsv
#
# Read-only by construction: the path list below contains only get*/check*/is* slugs, and the
# arguments sent are either none or an obviously nonexistent object name. Exit code is always 0;
# the matrix is the product. Columns: path  http  result  verdict  error
set -uo pipefail

host="${VZ_HOST:?set VZ_HOST}"
token="${VZ_TOKEN:?set VZ_TOKEN}"
# Deliberately no object names: an omitted envName makes the platform answer 705/2303 with the default
# context, which proves the method exists without ever naming - let alone targeting - a real object.

read_paths=$(cat <<'EOF'
/billing/account/rest/getaccount
/billing/account/rest/getquotas
/environment/binder/rest/getsslcerts
/environment/binder/rest/getdomains
/environment/build/rest/getprojects
/environment/control/rest/getallsumstatbyuid
/environment/control/rest/getbasicenvsinfo
/environment/control/rest/getcontainerenvvars
/environment/control/rest/getendpoints
/environment/control/rest/getenvinfo
/environment/control/rest/getenvs
/environment/control/rest/getlogslist
/environment/control/rest/getnodegroups
/environment/control/rest/getregions
/environment/control/rest/getsoftwarepackages
/environment/control/rest/getsshaccessinfo
/environment/control/rest/getstats
/environment/control/rest/getsumstat
/environment/control/rest/gettemplates
/environment/deployment/rest/getbuildprojects
/environment/deployment/rest/getdeployments
/environment/deployment/rest/gethooks
/environment/deployment/rest/getrepos
/environment/export/rest/getlist
/environment/file/rest/getfavorites
/environment/file/rest/getlist
/environment/file/rest/getmountpoints
/environment/group/rest/getgroups
/environment/nodegroup/rest/get
/environment/security/rest/getrules
/environment/tracking/rest/getaction
/environment/tracking/rest/getcurrentactions
/environment/tracking/rest/getserverutctime
/environment/tracking/rest/getuidactions
/environment/trigger/rest/getautoscalingtriggers
/environment/trigger/rest/gettriggers
/environment/vcs/rest/getproject
/marketplace/app/rest/getaddonlist
/marketplace/app/rest/getcategories
/marketplace/app/rest/getlist
/marketplace/favorite/rest/getlist
/marketplace/installation/rest/getsettings
/marketplace/jps/rest/getengineversion
/users/account/rest/getuserinfo
/users/authentication/rest/getsessions
/users/authentication/rest/gettokenapilist
/users/authentication/rest/gettokens
/users/collaboration/rest/getcollaborations
/users/collaboration/rest/getcollaborationresources
/users/collaboration/rest/getmembers
/users/collaboration/rest/getpolicies
/users/collaboration/rest/getroles
/utils/scheduler/rest/gettasks
EOF
)

verdict_of() {                       # result -> verdict
  case "$1" in
    0)   echo "callable" ;;
    2)   echo "forbidden-by-token" ;;
    3)   echo "param-needed" ;;
    705|2303) echo "needs-object" ;;
    702) echo "TOKEN-DEAD" ;;
    8)   echo "out-of-scope" ;;
    1702) echo "absent" ;;
    11)  echo "absent-or-invisible-env" ;;
    404) echo "absent" ;;
    *)   echo "other" ;;
  esac
}

printf 'path\thttp\tresult\tverdict\terror\n'
while IFS= read -r p; do
  [ -n "$p" ] || continue
  resp="$(curl -s --max-time 25 -G "https://${host}/1.0${p}" \
            --data-urlencode "session=${token}" -w $'\n%{http_code}' 2>/dev/null)" || true
  http="$(printf '%s' "$resp" | tail -1)"
  body="$(printf '%s' "$resp" | sed '$d')"
  if [ "$http" = "404" ] || printf '%s' "$body" | grep -qi 'Apache Tomcat'; then
    result="404"; error="no REST mapping on this build"
  else
    result="$(printf '%s' "$body" | grep -o '"result":[-0-9]*' | head -1 | cut -d: -f2)"
    [ -n "$result" ] || result="?"
    error="$(printf '%s' "$body" | grep -o '"error":"[^"]*"' | head -1 | cut -c10-90)"
  fi
  printf '%s\t%s\t%s\t%s\t%s\n' "$p" "$http" "$result" "$(verdict_of "$result")" "${error//	/ }"
  sleep 0.15
done <<< "$read_paths"
