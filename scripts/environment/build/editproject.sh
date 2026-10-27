#!/usr/bin/env bash
# Virtuozzo Application Management Platform API method wrapper (generated).
# path:     /environment/build/rest/editproject
# class:    write
# spec:     8.15 (tools/gen-scripts.py - do not edit; regenerate instead)
# required: envName, name, nodeid, path, projectid, type
# optional: keyId, login, password, env, context, branch, autoupdate, interval, autoResolveConflict, delay, hooks, workDir, targetNodeGroup
#
# Usage:  VZ_HOST=app.<platform> VZ_TOKEN=*** \
#           scripts/environment/build/editproject.sh envName=<value> name=<value> nodeid=<value> path=<value> projectid=<value> type=<value> [--dry-run]
# --dry-run prints the exact request without sending it.
# Write-class methods are refused by tools/vz-api.sh unless VZ_ALLOW_DESTRUCTIVE=1.
set -euo pipefail
exec "$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"/scripts/lib/method.sh \
  /environment/build/rest/editproject "envName name nodeid path projectid type" "$@"
