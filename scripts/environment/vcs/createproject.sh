#!/usr/bin/env bash
# Virtuozzo Application Management Platform API method wrapper (generated).
# path:     /environment/vcs/rest/createproject
# class:    write
# spec:     8.15 (tools/gen-scripts.py - do not edit; regenerate instead)
# required: context, envName, type, url
# optional: branch, keyId, login, password, autoupdate, interval, autoResolveConflict, zdt, updateNow, nodeGroup, hooks, delay, repoHash
#
# Usage:  VZ_HOST=app.<platform> VZ_TOKEN=*** \
#           scripts/environment/vcs/createproject.sh context=<value> envName=<value> type=<value> url=<value> [--dry-run]
# --dry-run prints the exact request without sending it.
# Write-class methods are refused by tools/vz-api.sh unless VZ_ALLOW_DESTRUCTIVE=1.
set -euo pipefail
exec "$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"/scripts/lib/method.sh \
  /environment/vcs/rest/createproject "context envName type url" "$@"
