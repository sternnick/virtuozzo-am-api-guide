#!/usr/bin/env bash
# Virtuozzo Application Management Platform API method wrapper (generated).
# path:     /environment/control/rest/getstats
# class:    read
# spec:     8.15 (tools/gen-scripts.py - do not edit; regenerate instead)
# required: duration, envName, interval
# optional: endtime, nodeid, nodetype, nodeGroup
#
# Usage:  VZ_HOST=app.<platform> VZ_TOKEN=*** \
#           scripts/environment/control/getstats.sh duration=<value> envName=<value> interval=<value> [--dry-run]
# --dry-run prints the exact request without sending it.
# Write-class methods are refused by tools/vz-api.sh unless VZ_ALLOW_DESTRUCTIVE=1.
set -euo pipefail
exec "$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"/scripts/lib/method.sh \
  /environment/control/rest/getstats "duration envName interval" "$@"
