#!/usr/bin/env bash
# Virtuozzo Application Management Platform API method wrapper (generated).
# path:     /environment/control/rest/editendpoint
# class:    write
# spec:     8.15 (tools/gen-scripts.py - do not edit; regenerate instead)
# required: envName, id, name, privatePort, protocol
# optional: -
#
# Usage:  VZ_HOST=app.<platform> VZ_TOKEN=*** \
#           scripts/environment/control/editendpoint.sh envName=<value> id=<value> name=<value> privatePort=<value> protocol=<value> [--dry-run]
# --dry-run prints the exact request without sending it.
# Write-class methods are refused by tools/vz-api.sh unless VZ_ALLOW_DESTRUCTIVE=1.
set -euo pipefail
exec "$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"/scripts/lib/method.sh \
  /environment/control/rest/editendpoint "envName id name privatePort protocol" "$@"
