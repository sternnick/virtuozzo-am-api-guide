#!/usr/bin/env bash
# Virtuozzo Application Management Platform API method wrapper (generated).
# path:     /utils/scheduler/rest/edittask
# class:    write
# spec:     8.15 (tools/gen-scripts.py - do not edit; regenerate instead)
# required: id, script, trigger
# optional: description, params
#
# Usage:  VZ_HOST=app.<platform> VZ_TOKEN=*** \
#           scripts/utils/scheduler/edittask.sh id=<value> script=<value> trigger=<value> [--dry-run]
# --dry-run prints the exact request without sending it.
# Write-class methods are refused by tools/vz-api.sh unless VZ_ALLOW_DESTRUCTIVE=1.
set -euo pipefail
exec "$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"/scripts/lib/method.sh \
  /utils/scheduler/rest/edittask "id script trigger" "$@"
