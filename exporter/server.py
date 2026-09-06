from flask import Flask, Response, jsonify

from .metrics_cache import MetricsCache
from .config_loader import load_config
from .file_checker import FileCheckerCache, calculate_integrity_score
from .logger import setup_logger


app = Flask(__name__)

# ---------------------------------------------------------
# Initialization
# ---------------------------------------------------------
config = load_config()
logger = setup_logger(config)

metrics_cache = MetricsCache(config)
file_checker_cache = FileCheckerCache(config)


# ---------------------------------------------------------
# Prometheus Metrics Formatting
# ---------------------------------------------------------
def format_prometheus(system_data, file_data):
    lines = []

    # System metrics
    for key, value in system_data.items():
        metric_name = f"system_{key}".replace(".", "_")
        lines.append(f"{metric_name} {value}")
        
    # NEW: system last update timestamp
    if "last_update_timestamp" in system_data:
        lines.append(f"system_metrics_last_update_timestamp {system_data['last_update_timestamp']}")
        
    # File checker metrics
    mismatches = file_data.get("mismatches", [])
    missing_remote = file_data.get("missing_remote", [])

    integrity_score = calculate_integrity_score(mismatches)

    lines.append(f"filechecker_integrity_score {integrity_score}")
    lines.append(f"filechecker_mismatch_count {len(mismatches)}")
    lines.append(f"filechecker_missing_remote_count {len(missing_remote)}")

    # NEW: file checker last scan timestamp
    if "last_scan_timestamp" in file_data:
        lines.append(f"filechecker_last_scan_timestamp {file_data['last_scan_timestamp']}")
        
    return "\n".join(lines)


# ---------------------------------------------------------
# Prometheus Endpoint
# ---------------------------------------------------------
@app.route("/metrics")
def metrics():
    system_data = metrics_cache.get_metrics()
    file_data = file_checker_cache.get_mismatch()
    output = format_prometheus(system_data, file_data)
    return Response(output, mimetype="text/plain")


# ---------------------------------------------------------
# File Checker Debug Endpoints
# ---------------------------------------------------------
@app.route("/filechecker")
def filechecker_debug():
    return jsonify({
        "local": file_checker_cache.get_files().get("local", []),
        "remote": file_checker_cache.get_files().get("remote", []),
        "comparison": file_checker_cache.get_mismatch()
    })


@app.route("/files")
def files():
    return jsonify(file_checker_cache.get_files())


@app.route("/mismatches")
def mismatches():
    return jsonify(file_checker_cache.get_mismatch().get("mismatches", []))


@app.route("/versions")
def versions():
    mismatches = file_checker_cache.get_mismatch().get("mismatches", [])
    version_drift = [
        m for m in mismatches
        if m.get("local_version") != m.get("remote_version")
    ]
    return jsonify(version_drift)


@app.route("/file-report")
def file_report():
    return jsonify(file_checker_cache.get_mismatch())


# ---------------------------------------------------------
# Health Endpoint
# ---------------------------------------------------------
@app.route("/health")
def health():
    return jsonify({"status": "ok"})


# ---------------------------------------------------------
# Debug Route: Show All Registered Routes
# ---------------------------------------------------------
@app.route("/debug-routes")
def debug_routes():
    return jsonify(sorted([rule.rule for rule in app.url_map.iter_rules()]))

@app.route("/ready")
def ready():
    system_ready = metrics_cache.last_update > 0
    file_ready = file_checker_cache.last_scan > 0

    if system_ready and file_ready:
        return jsonify({"status": "ready"}), 200
    else:
        return jsonify({"status": "initializing"}), 503

# ---------------------------------------------------------
# Main Entry
# ---------------------------------------------------------
if __name__ == "__main__":
    logger.info("Starting metrics exporter...")
    app.run(host=config["server"]["host"], port=config["server"]["port"])
