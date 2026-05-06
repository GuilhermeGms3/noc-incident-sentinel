# NOC Runbook

## Severity Model

- `P1`: Complete outage of critical service
- `P2`: Partial degradation or sustained high latency
- `P3`: Early warning (e.g. DNS slowness)

## Triage Checklist (0-15 min)

1. Confirm alert labels (`target_name`, `check_type`, `severity`).
2. Check `/status` endpoint from checker.
3. Validate target manually:
   - HTTP: `curl -I <url>`
   - TCP: `nc -zv <host> <port>`
   - DNS: `nslookup <domain>`

## Containment Actions

1. Open incident channel/ticket.
2. Route to responsible owner.
3. If false positive suspected, apply temporary silence in Alertmanager.

## Recovery Validation

1. Confirm `noc_target_up == 1`.
2. Confirm `noc_target_consecutive_failures == 0`.
3. Monitor latency for 10 minutes to ensure stability.

## Post-Incident

1. Document root cause and timeline.
2. Add or tune alert rule thresholds.
3. Update this runbook with lessons learned.
