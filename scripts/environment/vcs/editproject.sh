#!/usr/bin/env bash
# Virtuozzo Application Management Platform API method wrapper (generated).
# path:     /environment/vcs/rest/editproject
# class:    write
# spec:     8.15 (tools/gen-scripts.py - do not edit; regenerate instead)
# required: autoResolveConflict, autoupdate, envName, newcontext, oldcontext, type, url, zdt
# optional: branch, keyId, login, password, interval, nodeGroup, hooks, delay, repoHash
#
# Usage:  VZ_HOST=app.<platform> VZ_TOKEN=*** \
#           scripts/environment/vcs/editproject.sh autoResolveConflict=<value> autoupdate=<value> envName=<value> newcontext=<value> oldcontext=<value> type=<value> url=<value> zdt=<value> [--dry-run]
# --dry-run prints the exact request without sending it.
# Write-class methods are refused by tools/vz-api.sh unless VZ_ALLOW_DESTRUCTIVE=1.
set -euo pipefail
exec "$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"/scripts/lib/method.sh \
  /environment/vcs/rest/editproject "autoResolveConflict autoupdate envName newcontext oldcontext type url zdt" "$@"
