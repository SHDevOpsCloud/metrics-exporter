import logging
import os

def setup_logger(config):
    log_cfg = config.get("logging", {})
    enabled = log_cfg.get("enabled", True)
    level = log_cfg.get("level", "INFO").upper()

    logger = logging.getLogger("file_checker")
    logger.setLevel(level)

    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s",
        "%Y-%m-%d %H:%M:%S"
    )

    # console handler
    console = logging.StreamHandler()
    console.setFormatter(formatter)
    logger.addHandler(console)

    # file handler
    if enabled and log_cfg.get("file"):
        log_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), log_cfg["file"])
        file_handler = logging.FileHandler(log_path)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger
