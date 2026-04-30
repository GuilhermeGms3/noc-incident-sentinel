from flask import Flask, Response
from prometheus_client import Gauge, generate_latest, CONTENT_TYPE_LATEST
import requests
import socket
import time
import yaml

app = Flask(__name__)

up_metric = Gauge('noc_target_up', 'Target availability', ['target_name', 'target', 'check_type'])
latency_metric = Gauge('noc_target_latency_ms', 'Target latency in ms', ['target_name', 'target', 'check_type'])


def check_http(target: str, timeout: int) -> tuple[int, float]:
    start = time.time()
    try:
        res = requests.get(target, timeout=timeout)
        latency = (time.time() - start) * 1000
        return (1 if res.status_code < 500 else 0, latency)
    except Exception:
        return (0, -1)


def check_tcp(target: str, timeout: int) -> tuple[int, float]:
    host, port = target.split(':')
    port = int(port)
    start = time.time()
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    try:
        s.connect((host, port))
        latency = (time.time() - start) * 1000
        s.close()
        return (1, latency)
    except Exception:
        return (0, -1)


def run_checks() -> None:
    with open('/app/targets.yaml', 'r', encoding='utf-8') as f:
        cfg = yaml.safe_load(f)

    for t in cfg.get('targets', []):
        name = t['name']
        ctype = t['type']
        target = t['target']
        timeout = int(t.get('timeout_seconds', 5))

        if ctype == 'http':
            up, latency = check_http(target, timeout)
        elif ctype == 'tcp':
            up, latency = check_tcp(target, timeout)
        else:
            up, latency = (0, -1)

        up_metric.labels(target_name=name, target=target, check_type=ctype).set(up)
        latency_metric.labels(target_name=name, target=target, check_type=ctype).set(latency)


@app.route('/metrics')
def metrics() -> Response:
    run_checks()
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)


@app.route('/health')
def health() -> dict:
    return {'status': 'ok'}


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9115)
