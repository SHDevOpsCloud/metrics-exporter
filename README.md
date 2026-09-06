# Metrics Exporter

A lightweight Python microservice that exposes system metrics in Prometheus format. Designed for DevOps workflows, monitoring stacks, and systemd service deployment. Metrics are refreshed every 5 seconds in a background thread to ensure smooth, consistent performance.

## Features
- CPU usage (percent)
- Memory usage (percent, bytes, MB, GB)
- Disk usage (percent, bytes, MB, GB)
- Background refresh every 5 seconds
- `/metrics` endpoint for Prometheus
- `/health` endpoint for basic status
- Clean, extensible architecture for future enhancements

## Installation
pip install -r requirements.txt

## Run
python main.py


The service will start on port **8000**.

## Endpoints

### `/metrics`
Returns Prometheus‑formatted system metrics.

### `/health`
Simple JSON health check.

## Example Output
system_cpu_usage_percent 12.5
system_memory_usage_percent 63.2
system_memory_used_bytes 842137600
system_memory_total_bytes 1331691520
system_memory_used_mb 803.0
system_memory_total_mb 1269.0
system_memory_used_gb 0.78
system_memory_total_gb 1.24
system_disk_usage_percent 71.1
system_disk_used_bytes 1234567890
system_disk_total_bytes 2345678901
system_disk_used_mb 1177.0
system_disk_total_mb 2238.0
system_disk_used_gb 1.15
system_disk_total_gb 2.18


## Project Structure
metrics-exporter/
├── exporter/
│   ├── system_metrics.py
│   ├── metrics_cache.py
│   └── server.py
├── main.py
├── requirements.txt
└── README.md


## Future Enhancements
- Full file integrity checker (timestamps, size, version metadata)
- DLL version mismatch detection
- Windows share / remote directory comparison
- Additional endpoints (`/files`, `/mismatch`)
- Configurable refresh interval
- Unit tests and CI integration

