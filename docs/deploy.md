# Deployment (Tailscale VM)

## 1) Install Docker (if needed)

```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
```

## 2) Clone and run

```bash
git clone https://github.com/GuilhermeGms3/noc-incident-sentinel.git
cd noc-incident-sentinel
docker compose up -d --build
```

## 3) Validate

```bash
curl http://localhost:9115/health
curl http://localhost:9115/status
curl http://localhost:9115/metrics | head
curl http://localhost:9091/-/healthy
curl http://localhost:9093/-/healthy
```

## 4) Grafana integration

- Add Prometheus data source: `http://<vm-ip>:9091`
- Build panel with `noc_target_up` and `noc_target_latency_ms`

## 5) N8N webhook

Alertmanager receiver points to:

`http://100.102.45.127:5678/webhook/noc-alert`

Create this webhook workflow in N8N to route notifications.
