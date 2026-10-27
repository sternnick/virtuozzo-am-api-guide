# 6. Read-only recipes

All of these are safe against a production platform: they are `get*`-shaped, they mutate nothing, and
they are the calls used to produce these notes. Set the two variables first:

```bash
export VZ_HOST="app.${PLATFORM_DOMAIN}"
export VZ_TOKEN="..."
alias vz='./tools/vz-api.sh'
```

## Identity, build, liveness

```bash
vz /users/account/rest/getuserinfo | jq '{uid, accessType, email: .email, authType: .authConfig.type}'
vz /marketplace/jps/rest/getengineversion | jq .version          # platform build
vz /environment/tracking/rest/getserverutctime                   # clock, useful before log queries
```

`accessType` is the account-level role. `authConfig.type` tells you whether the account runs 2FA, which
explains why a session-based script cannot log in unattended.

## What exists

```bash
vz /environment/control/rest/getenvs | jq -r '.infos[].env | [.envName, .domain, .status] | @tsv'
vz /environment/control/rest/getbasicenvsinfo | jq '[.infos[].nodes[].nodeType] | group_by(.) | map({(.[0]): length}) | add'
vz /environment/control/rest/getregions | jq -r '.regions[] | [.name, .country] | @tsv'
vz /environment/group/rest/getgroups | jq '.groups | length'
```

`getenvs` is the heavy one: it returns the full node description for every environment, which is the
cheapest single request that explains a platform. Expect node fields such as `nodeType`, `engineType`,
`engineVersion`, `dockerOs`, `intIP`, `ctid`, `endpoints`, `cpu`, `ram`, `hdd`, `fixedCloudlets`,
`flexibleCloudlets`. It can be tens of kilobytes on a real account; pipe it through `jq`, do not paste
it into a ticket.

One environment, in detail:

```bash
vz /environment/control/rest/getenvinfo --param envName="${ENV_NAME}" \
  | jq '{envGroups, nodes: [.nodes[] | {name, nodeType, state, cpu, ram, hdd, intIP}]}'
```

If you get `result: 705` here, the environment exists and your token's user simply is not on it.

## Cost and quota

```bash
vz /billing/account/rest/getaccount | jq '{balance, currency, email, startDate}'
vz /billing/account/rest/getquotas  | jq -r '.array[].quota | [.name, .value] | @tsv' | head -30
vz /billing/account/rest/getextendedaccountbillinghistorybyperiod \
   --param starttime="2026-01-01 00:00:00" --param endtime="2026-01-31 23:59:59"
```

`getquotas` names are prefixed (`account.minbalance`, `env.cpu.limit`, ...) and are the numbers behind
"why did the platform refuse to scale that node".

## Who has access

```bash
vz /users/collaboration/rest/getmembers             | jq -r '.array[] | [.displayName, .memberUid, .type] | @tsv'
vz /users/collaboration/rest/getcollaborations      | jq '.array | length'
vz /users/collaboration/rest/getroles               | jq -r '.roles[] | [.uniqueName, .name] | @tsv'
vz /users/collaboration/rest/getpolicies            | jq -r '.policies[] | .uniqueName' | head
vz /users/collaboration/rest/getcollaborationresources | jq '.resources | length'
```

This is the fastest way to answer "does automation have a path into an environment it should not have".

## Nodes, containers, logs, statistics (all need a target)

```bash
vz /environment/control/rest/getnodegroups     --param envName="${ENV_NAME}"
vz /environment/control/rest/getendpoints      --param envName="${ENV_NAME}"
vz /environment/control/rest/getcontainerenvvars --param envName="${ENV_NAME}" --param nodeGroup=cp
vz /environment/control/rest/getlogslist       --param envName="${ENV_NAME}" --param nodeGroup=cp
vz /environment/control/rest/getlogs           --param envName="${ENV_NAME}" --param nodeGroup=cp \
   --param fromDate="2026-01-01" --param toDate="2026-01-02" | jq '.logs | length'
vz /environment/control/rest/getstats          --param envName="${ENV_NAME}" --param nodeGroup=cp
vz /environment/control/rest/getsshaccessinfo  --param envName="${ENV_NAME}"
```

Two cautions: `getlogs` output can be large enough to fill a chat window, and
`getcontainerenvvars` returns whatever your deployment stored there, which is where secrets usually
live. Filter with `jq` before you show the output to anyone or write it to a file.

## Builds, deployments, marketplace

```bash
vz /environment/deployment/rest/getrepos
vz /environment/deployment/rest/getbuildprojects --param envName="${ENV_NAME}"
vz /environment/deployment/rest/getdeployments   --param envName="${ENV_NAME}" --param nodeGroup=cp
vz /environment/build/rest/getprojects           --param envName="${ENV_NAME}"
vz /marketplace/app/rest/getcategories
vz /marketplace/jps/rest/getappinfo --param jps='{"name":"nginx","version":"latest"}'
```

## Asynchronous work and scheduled jobs

```bash
vz /environment/tracking/rest/getcurrentactions | jq '.array | length'
vz /environment/tracking/rest/getuidactions     | jq '.array | length'
vz /utils/scheduler/rest/gettasks               | jq -r '.objects[] | [.appid, .status] | @tsv'
```

`getcurrentactions` returning an empty array is the clean signal that nobody is mutating the platform
right now. Check it before anything you consider risky, even though your own token cannot be the cause.

## The capability scan, in one line

```bash
./tools/vz-capability-scan.sh | tee capability.tsv | column -t
```

Output columns are `path`, `http`, `result`, `verdict`, `error`. It never issues a non-read call, so it
is safe to run against a platform you only have read business on.

## A useful negative list

These slugs looked plausible and are **not** mapped on the tested build (they answer HTML 404 or `1702`).
Re-verify before you rely on this: it is a statement about one build, not a specification.

```
/1.0/environment/control/rest/getlist            /1.0/environment/control/rest/getstate
/1.0/environment/control/rest/findbyname         /1.0/environment/control/rest/getdomains
/1.0/environment/control/rest/getaccountenvs     /1.0/environment/control/rest/getcustomdomains
/1.0/environment/control/rest/getcndomainbindings /1.0/environment/control/rest/restartenv
/1.0/environment/control/rest/destroyenv         /1.0/environment/control/rest/deploy
/1.0/environment/control/rest/getinstalllog      /1.0/environment/control/rest/getregionpricing
/1.0/utils/batch/call                            /1.0/marketplace/installation/rest/getlist
```

Useful replacements on that same build: `getenvs` and `getbasicenvsinfo` instead of `getlist`;
`getenvinfo` instead of `getstate` / `findbyname`; `environment/binder/rest/getdomains` with an
`envName` instead of the account-wide domain listing; `getsslcerts` for certificate inventory.
