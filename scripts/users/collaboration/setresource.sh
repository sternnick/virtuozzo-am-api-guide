#!/usr/bin/env bash
# Virtuozzo Application Management Platform API method wrapper (generated).
# path:     /users/collaboration/rest/setresource
# class:    write
# spec:     8.15 (tools/gen-scripts.py - do not edit; regenerate instead)
# required: collaborationId, resourceId, roleIds
# optional: resourceType, ownerUid, createRoleIfNeeded
#
# Usage:  VZ_HOST=app.<platform> VZ_TOKEN=*** \
#           scripts/users/collaboration/setresource.sh collaborationId=<value> resourceId=<value> roleIds=<value> [--dry-run]
# --dry-run prints the exact request without sending it.
# Write-class methods are refused by tools/vz-api.sh unless VZ_ALLOW_DESTRUCTIVE=1.
set -euo pipefail
exec "$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"/scripts/lib/method.sh \
  /users/collaboration/rest/setresource "collaborationId resourceId roleIds" "$@"
