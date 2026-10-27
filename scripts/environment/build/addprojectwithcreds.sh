#!/usr/bin/env bash
# Virtuozzo Application Management Platform API method wrapper (generated).
# path:     /environment/build/rest/addprojectwithcreds
# class:    write
# spec:     8.15 (tools/gen-scripts.py - do not edit; regenerate instead)
# required: autoResolveConflict, autoUpdate, envName, name, nodeId, path, type
# optional: targetEnv, login, password, context, branch, interval, delay, deployNow, hooks, workDir
#
# Usage:  VZ_HOST=app.<platform> VZ_TOKEN=*** \
#           scripts/environment/build/addprojectwithcreds.sh autoResolveConflict=<value> autoUpdate=<value> envName=<value> name=<value> nodeId=<value> path=<value> type=<value> [--dry-run]
# --dry-run prints the exact request without sending it.
# Write-class methods are refused by tools/vz-api.sh unless VZ_ALLOW_DESTRUCTIVE=1.
set -euo pipefail
exec "$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"/scripts/lib/method.sh \
  /environment/build/rest/addprojectwithcreds "autoResolveConflict autoUpdate envName name nodeId path type" "$@"
