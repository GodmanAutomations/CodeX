# Trello Route Stops Command - 2026-06-16

## Outcome

Added a Trello-aware route helper for Stephen's pool stops.

- Local command: `/Users/stephengodman/CodeX/bin/trello-route-stops`
- Global shortcut: `/Users/stephengodman/bin/trello-route-stops`
- MCP tool: `route_pool_stops`

The command can:

- Resolve Trello card names to customer/job cards.
- Pull route addresses from work-order attachment names.
- Add fixed manual stops with `--manual-stop NAME=ADDRESS`.
- Put the warehouse first with `--warehouse-first`.
- Optimize driving order with warehouse fixed first.
- Save local route notes under `/Users/stephengodman/CodeX/work-artifacts/routes/`.

## Current Route

Stephen corrected:

- Warehouse: `3765 Winchester Rd, Memphis, TN`
- Keathley pump/drop: `8925 Cedar Mills Cove, Cordova, TN`

Verified route:

1. Warehouse - `3765 Winchester Rd, Memphis, TN`
2. Chris Corson - `1111 Tuscumbia Road, Collierville, TN`
3. Corinne Cave - `909 Valleyview Lane, Collierville, TN`
4. Juan Santiago - `9822 Frank Road, Germantown, TN`
5. Keathley pump drop - `8925 Cedar Mills Cove, Cordova, TN`

Estimated before live traffic:

- Distance: `33.6` miles
- Drive time: `65.1` minutes

## Safety

- Trello writes: none
- Google Drive writes: none
- Pi5 writes: none
- Secrets printed: none

## Verification

Verified with:

- Python compile check on `trello-route-stops` and the Trello MCP server.
- Live command run using corrected warehouse/manual Keathley stop plus Trello stops for Corson, Santiago, and Cave.
- Direct MCP wrapper call through `route_pool_stops`.
- MCP inventory confirmed `route_pool_stops` is exposed as read-only.
