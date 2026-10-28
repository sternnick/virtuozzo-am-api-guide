#!/usr/bin/env bash
# Virtuozzo Application Management Platform API method wrapper (generated).
# path:     /utils/scheduler/rest/createenvtask
# class:    write
# spec:     8.15 (tools/gen-scripts.py - do not edit; regenerate instead)
# required: script, trigger
# optional: envName, description, params
#
# Usage:  VZ_HOST=app.<platform> VZ_TOKEN=*** \
#           scripts/utils/scheduler/createenvtask.sh script=<value> trigger=<value> [--dry-run]
# --dry-run prints the exact request without sending it.
# Write-class methods are refused by tools/vz-api.sh unless VZ_ALLOW_DESTRUCTIVE=1.
set -euo pipefail
exec "$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"/scripts/lib/method.sh \
  /utils/scheduler/rest/createenvtask "script trigger" "$@"
