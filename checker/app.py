from flask import Flask, Response, jsonify
from prometheus_client import Gauge, generate_latest, CONTENT_TYPE_LATEST
import requests
import socket
import time
import yaml
from urllib.parse import urlparse

app = Flask(__name__)

up_metric = Gauge('noc_target_up', 'Target availability', ['target_name', 'target', 'check_type'])
latency_metric = Gauge('noc_target_latency_ms', 'Target latency in ms', ['target_name', 'target', 'check_type'])
last_check_metric = Gauge('noc_target_last_check_unixtime', 'Last successful check timestamp', ['target_name', 'target', 'check_type'])
consecutive_failures_metric = Gauge('noc_target_consecutive_failures', 'Consecutive failure count per target', ['target_name', 'target', 'check_type'])

LAST_RESULTS: list[dict] = []
FAIL_COUNTERS: dict[tuple[str, str, str], int] = {}


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


def check_dns(target: str, timeout: int) -> tuple[int, float]:
    # DNS check resolves a hostname to IP and measures lookup latency.
    start = time.time()
    default_timeout = socket.getdefaulttimeout()
    socket.setdefaulttimeout(timeout)
    try:
        socket.gethostbyname(target)
        latency = (time.time() - start) * 1000
        return (1, latency)
    except Exception:
        return (0, -1)
    finally:
        socket.setdefaulttimeout(default_timeout)


def target_display_name(ctype: str, target: str) -> str:
    if ctype == 'http':
        parsed = urlparse(target)
        return parsed.netloc or target
    return target


def run_single_check(ctype: str, target: str, timeout: int) -> tuple[int, float]:
    if ctype == 'http':
        return check_http(target, timeout)
    if ctype == 'tcp':
        return check_tcp(target, timeout)
    if ctype == 'dns':
        return check_dns(target, timeout)
    return (0, -1)


def check_with_retries(ctype: str, target: str, timeout: int, retries: int) -> tuple[int, float]:
    attempts = max(1, retries)
    last_latency = -1.0
    for _ in range(attempts):
        up, latency = run_single_check(ctype, target, timeout)
        last_latency = latency
        if up == 1:
            return (up, latency)
    return (0, last_latency)


def run_checks() -> None:
    global LAST_RESULTS
    with open('/app/targets.yaml', 'r', encoding='utf-8') as f:
        cfg = yaml.safe_load(f)

    results: list[dict] = []
    for t in cfg.get('targets', []):
        name = t['name']
        ctype = t['type']
        target = t['target']
        timeout = int(t.get('timeout_seconds', 5))
        retries = int(t.get('retries', 2))
        up, latency = check_with_retries(ctype, target, timeout, retries)

        up_metric.labels(target_name=name, target=target, check_type=ctype).set(up)
        latency_metric.labels(target_name=name, target=target, check_type=ctype).set(latency)
        last_check_metric.labels(target_name=name, target=target, check_type=ctype).set(time.time())
        failure_key = (name, target, ctype)
        if up == 1:
            FAIL_COUNTERS[failure_key] = 0
        else:
            FAIL_COUNTERS[failure_key] = FAIL_COUNTERS.get(failure_key, 0) + 1
        consecutive_failures_metric.labels(target_name=name, target=target, check_type=ctype).set(
            FAIL_COUNTERS[failure_key]
        )
        results.append(
            {
                'name': name,
                'target': target,
                'target_display': target_display_name(ctype, target),
                'check_type': ctype,
                'retries': retries,
                'up': bool(up),
                'latency_ms': round(latency, 2),
                'consecutive_failures': FAIL_COUNTERS[failure_key],
            }
        )
    LAST_RESULTS = results


@app.route('/metrics')
def metrics() -> Response:
    run_checks()
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)


@app.route('/health')
def health() -> dict:
    return {'status': 'ok'}


@app.route('/status')
def status() -> Response:
    run_checks()
    down_count = len([r for r in LAST_RESULTS if not r['up']])
    return jsonify(
        {
            'status': 'degraded' if down_count > 0 else 'healthy',
            'timestamp': int(time.time()),
            'down_count': down_count,
            'targets': LAST_RESULTS,
        }
    )


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9115)
