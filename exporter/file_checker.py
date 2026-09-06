import os
import fnmatch
import threading
import time
from datetime import datetime

from .logger import setup_logger

try:
    import win32api
except ImportError:
    win32api = None  # Linux or missing dependency


# -----------------------------
# Helpers
# -----------------------------

def bytes_to_mb(value):
    return value / (1024 * 1024)


def bytes_to_gb(value):
    return value / (1024 * 1024 * 1024)


def get_file_version(path):
    """Windows-only file version extraction."""
    if not win32api:
        return None

    try:
        info = win32api.GetFileVersionInfo(path, "\\")
        ms = info["FileVersionMS"]
        ls = info["FileVersionLS"]
        return f"{ms >> 16}.{ms & 0xFFFF}.{ls >> 16}.{ls & 0xFFFF}"
    except Exception:
        return None


def list_files(base_path, include_patterns=None, exclude_patterns=None):
    """Scan a directory and return file metadata."""
    results = []

    if not os.path.exists(base_path):
        return results

    for root, dirs, files in os.walk(base_path):
        for name in files:
            full_path = os.path.join(root, name)

            # Include filter
            if include_patterns:
                if not any(fnmatch.fnmatch(name, pat) for pat in include_patterns):
                    continue

            # Exclude filter
            if exclude_patterns:
                if any(fnmatch.fnmatch(name, pat) for pat in exclude_patterns):
                    continue

            stat = os.stat(full_path)

            results.append({
                "name": name,
                "path": full_path,
                "size_bytes": stat.st_size,
                "modified_ts": stat.st_mtime,
                "version": get_file_version(full_path),
            })

    return results


def compare_file_sets(local_files, remote_files):
    """Compare two file lists and detect mismatches."""
    local_map = {f["name"]: f for f in local_files}
    remote_map = {f["name"]: f for f in remote_files}

    mismatches = []
    missing_remote = []

    for name, lf in local_map.items():
        rf = remote_map.get(name)

        if not rf:
            missing_remote.append({
                "name": name,
                "path": lf["path"],
                "severity": "CRITICAL",
            })
            continue

        size_drift = abs(lf["size_bytes"] - rf["size_bytes"])
        ts_drift = abs(lf["modified_ts"] - rf["modified_ts"])
        version_drift = 1 if lf.get("version") != rf.get("version") else 0

        severity = "OK"
        if size_drift > 0 or ts_drift > 0 or version_drift > 0:
            severity = "WARNING"

        mismatches.append({
            "name": name,
            "local_size_bytes": lf["size_bytes"],
            "remote_size_bytes": rf["size_bytes"],
            "local_modified_ts": lf["modified_ts"],
            "remote_modified_ts": rf["modified_ts"],
            "local_version": lf.get("version"),
            "remote_version": rf.get("version"),
            "severity": severity,
        })

    return {
        "mismatches": mismatches,
        "missing_remote": missing_remote,
    }


# -----------------------------
# Integrity Score (TOP LEVEL)
# -----------------------------

def calculate_integrity_score(mismatches):
    """Compute a 0–100 score based on drift and severity."""
    score = 100

    critical = sum(1 for m in mismatches if m["severity"] == "CRITICAL")
    warning = sum(1 for m in mismatches if m["severity"] == "WARNING")

    total_size_drift_mb = 0
    total_timestamp_drift_hours = 0

    for m in mismatches:
        size_drift = abs(m["local_size_bytes"] - m["remote_size_bytes"])
        ts_drift = abs(m["local_modified_ts"] - m["remote_modified_ts"])

        total_size_drift_mb += bytes_to_mb(size_drift)
        total_timestamp_drift_hours += ts_drift / 3600

    # Penalties
    score -= critical * 20
    score -= warning * 5
    score -= total_size_drift_mb * 1
    score -= total_timestamp_drift_hours * 1

    return max(0, min(100, round(score, 2)))


# -----------------------------
# FileCheckerCache Class
# -----------------------------

class FileCheckerCache:
    def __init__(self, config):
        self.local_dir = config["file_checker"]["local_directory"]
        self.remote_dir = config["file_checker"]["remote_directory"]
        self.interval = config["file_checker"]["scan_interval"]
			
        self.config = config
        self.local_files = []
        self.remote_files = []
        self.comparison = {}
        self.last_scan = 0
        
        self.scan_interval = config["file_checker"]["scan_interval"]
        self.logger = setup_logger(config)

        self._start_background_scanner()

    def _start_background_scanner(self):
        thread = threading.Thread(target=self._scan_loop, daemon=True)
        thread.start()

    def _scan_loop(self):
        while True:
            fc = self.config["file_checker"]

            local_dir = fc["local_directory"]
            remote_dir = fc["remote_directory"]
            include = fc["include_patterns"]
            exclude = fc["exclude_patterns"]

            self.logger.info("Scanning file directories...")

            # Scan local + remote
            self.local_files = list_files(local_dir, include, exclude)
            self.remote_files = list_files(remote_dir, include, exclude)

            self.logger.info(f"Local files found: {len(self.local_files)}")
            self.logger.info(f"Remote files found: {len(self.remote_files)}")

            # Compare results
            self.comparison = compare_file_sets(self.local_files, self.remote_files)
            
            #NEW: update timestamp
            self.last_scan = int(time.time())

            # Log missing remote files
            for f in self.comparison["missing_remote"]:
                self.logger.warning(
                    f"Missing remote file: {f['name']} ({f['path']})"
                )

            # Log mismatches
            for m in self.comparison["mismatches"]:
                if m["severity"] != "OK":
                    size_drift = abs(m["local_size_bytes"] - m["remote_size_bytes"])
                    version_drift = (
                        1 if m.get("local_version") != m.get("remote_version") else 0
                    )
                    ts_drift = abs(m["local_modified_ts"] - m["remote_modified_ts"])

                    self.logger.error(
                        f"[{m['severity']}] Mismatch: {m['name']} | "
                        f"size drift={size_drift} bytes | "
                        f"version drift={version_drift} | "
                        f"timestamp drift={ts_drift} seconds"
                    )

            time.sleep(self.scan_interval)

    def get_files(self):
        return {
            "local": self.local_files,
            "remote": self.remote_files,
        }

    def get_mismatch(self):
        return {
            **self.comparison,
            "last_scan_timestamp": self.last_scan
        }
