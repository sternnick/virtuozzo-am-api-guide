#!/usr/bin/env bash
# Virtuozzo Application Management Platform API method wrapper (generated).
# path:     /users/collaboration/rest/addpolicy
# class:    write
# spec:     8.15 (tools/gen-scripts.py - do not edit; regenerate instead)
# required: methods, name
# optional: description
#
# Usage:  VZ_HOST=app.<platform> VZ_TOKEN=*** \
#           scripts/users/collaboration/addpolicy.sh methods=<value> name=<value> [--dry-run]
# --dry-run prints the exact request without sending it.
# Write-class methods are refused by tools/vz-api.sh unless VZ_ALLOW_DESTRUCTIVE=1.
set -euo pipefail
exec "$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"/scripts/lib/method.sh \
  /users/collaboration/rest/addpolicy "methods name" "$@"
