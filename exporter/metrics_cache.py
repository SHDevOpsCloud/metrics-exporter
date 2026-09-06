import time
import threading

from .system_metrics import collect_system_metrics
from .logger import setup_logger


class MetricsCache:
    """
    Background-cached system metrics collector.
    Prometheus scrapes this via /metrics.
    """

    def __init__(self, config):
        self.config = config
        self.metrics = {}
        self.interval = config["metrics"]["collection_interval"]
        self.logger = setup_logger(config)
        self.last_update = 0

        self._start_background_collector()

    def _start_background_collector(self):
        thread = threading.Thread(target=self._collection_loop, daemon=True)
        thread.start()

    def _collection_loop(self):
        while True:
            try:
                self.metrics = collect_system_metrics()
                
                #NEW: update timestamp
                self.last_update = int(time.time())
                
                self.logger.info("System metrics updated.")
            except Exception as e:
                self.logger.error(f"Metrics collection failed: {e}")

            time.sleep(self.interval)   

    def get_metrics(self):
        return {
            **self.metrics,
            "last_update_timestamp": self.last_update
        }
