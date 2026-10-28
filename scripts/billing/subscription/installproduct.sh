#!/usr/bin/env bash
# Virtuozzo Application Management Platform API method wrapper (generated).
# path:     /billing/subscription/rest/installproduct
# class:    write
# spec:     8.15 (tools/gen-scripts.py - do not edit; regenerate instead)
# required: subscriptionId
# optional: itemId, settings, envName, displayName, envGroups, region, lang
#
# Usage:  VZ_HOST=app.<platform> VZ_TOKEN=*** \
#           scripts/billing/subscription/installproduct.sh subscriptionId=<value> [--dry-run]
# --dry-run prints the exact request without sending it.
# Write-class methods are refused by tools/vz-api.sh unless VZ_ALLOW_DESTRUCTIVE=1.
set -euo pipefail
exec "$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"/scripts/lib/method.sh \
  /billing/subscription/rest/installproduct "subscriptionId" "$@"
