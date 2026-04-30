# NOC Incident Sentinel

Lightweight NOC incident orchestration layer on top of Prometheus + Grafana.

## What it does

- Probes critical services (HTTP/port checks).
- Exposes metrics for Prometheus scraping.
- Applies alert rules for downtime and high latency.
- Routes incidents to webhooks (N8N/Telegram/Slack).

## Stack

- Python 3.11
- Flask + Prometheus client
- Prometheus + Alertmanager
- Grafana (existing in your environment)

## Quick Start

```bash
docker compose up -d
```

Services:

- Checker API: `http://localhost:9115/metrics`
- Prometheus: `http://localhost:9091`
- Alertmanager: `http://localhost:9093`

## Configure targets

Edit `checker/targets.yaml`:

```yaml
targets:
  - name: edge-proxy
    type: http
    target: http://100.72.95.93
    timeout_seconds: 5
```

## Incident flow

1. Checker probes targets and emits metrics.
2. Prometheus scrapes metrics and evaluates rules.
3. Alertmanager sends webhook payload to N8N.
4. N8N routes notifications/escalation.

## Next steps

- Add ping + DNS probes.
- Add maintenance windows and silences.
- Add runbook links per alert.
