# Observability Demo (Prometheus + Loki + Tempo + Grafana)

Server 1 (app): frontend, order-service, inventory-service, payment-service + Grafana Alloy
Server 2 (monitoring): Prometheus, Loki, Tempo, Grafana

Flow: Alloy scrapes /metrics (-> Prometheus remote_write), reads Docker logs (-> Loki),
receives OTLP traces (-> Tempo). Grafana reads all three.

## Deploy
Prerequisite on both servers: Docker + Docker Compose plugin.

### 1. Server 2 first
    cd server2
    GRAFANA_PASSWORD=choose_a_password docker compose up -d
Open firewall on server2 ONLY for server1's IP: 9090, 3100, 4317.
Grafana (3000) open for your own access.

### 2. Server 1
    cd server1
    cp .env.example .env     # set SERVER2_IP=<server2 private/public ip>
    docker compose up -d --build
App: http://SERVER1_IP  (port 80). Alloy UI: http://SERVER1_IP:12345 (restrict this port).

### 3. Generate traffic
    ./loadgen.sh http://localhost      # or just click the buttons in the UI

## View in Grafana (http://SERVER2_IP:3000, user admin)
- Dashboards > Demo > "Demo Shop Overview": request rate, error rate, p95 latency, logs
- Logs: click a log line, then the TraceID link opens the trace in Tempo
- Traces: Explore > Tempo > Search by service; use "Logs for this span" to jump to Loki

## Quick checks
- Prometheus: http://SERVER2_IP:9090 -> query `http_requests_total`
- Loki: Explore > Loki > `{service="order-service"}`
- Tempo: Explore > Tempo > Search
- Alloy not sending? `docker compose logs alloy` on server1 and test `nc -zv SERVER2_IP 9090 3100 4317`

## Notes
- Data retention is 7 days. Stored in Docker volumes.
- Demo only: no TLS/auth between servers, so keep ports firewalled to server1.
