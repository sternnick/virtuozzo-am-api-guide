#!/usr/bin/env bash
# Virtuozzo Application Management Platform API method wrapper (generated).
# path:     /environment/file/rest/addmountpointbyid
# class:    write
# spec:     8.15 (tools/gen-scripts.py - do not edit; regenerate instead)
# required: envName, nodeId, path, sourcePath
# optional: protocol, sourceHost, sourceNodeId, name, readOnly, sourceAddressType
#
# Usage:  VZ_HOST=app.<platform> VZ_TOKEN=*** \
#           scripts/environment/file/addmountpointbyid.sh envName=<value> nodeId=<value> path=<value> sourcePath=<value> [--dry-run]
# --dry-run prints the exact request without sending it.
# Write-class methods are refused by tools/vz-api.sh unless VZ_ALLOW_DESTRUCTIVE=1.
set -euo pipefail
exec "$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"/scripts/lib/method.sh \
  /environment/file/rest/addmountpointbyid "envName nodeId path sourcePath" "$@"
