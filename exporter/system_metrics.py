import psutil

def bytes_to_mb(value):
    return value / (1024 * 1024)

def bytes_to_gb(value):
    return value / (1024 * 1024 * 1024)

def collect_system_metrics():
    metrics = {}

    # CPU
    metrics["system_cpu_usage_percent"] = psutil.cpu_percent(interval=None)

    # Memory
    mem = psutil.virtual_memory()
    metrics["system_memory_usage_percent"] = mem.percent
    metrics["system_memory_used_bytes"] = mem.used
    metrics["system_memory_total_bytes"] = mem.total
    metrics["system_memory_used_mb"] = bytes_to_mb(mem.used)
    metrics["system_memory_total_mb"] = bytes_to_mb(mem.total)
    metrics["system_memory_used_gb"] = bytes_to_gb(mem.used)
    metrics["system_memory_total_gb"] = bytes_to_gb(mem.total)

    # Disk
    disk = psutil.disk_usage("/")
    metrics["system_disk_usage_percent"] = disk.percent
    metrics["system_disk_used_bytes"] = disk.used
    metrics["system_disk_total_bytes"] = disk.total
    metrics["system_disk_used_mb"] = bytes_to_mb(disk.used)
    metrics["system_disk_total_mb"] = bytes_to_mb(disk.total)
    metrics["system_disk_used_gb"] = bytes_to_gb(disk.used)
    metrics["system_disk_total_gb"] = bytes_to_gb(disk.total)

    return metrics
