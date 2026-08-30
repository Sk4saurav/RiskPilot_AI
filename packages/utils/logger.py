import logging

def setup_logger(name: str):
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(levelname)s %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger

def log_event(logger, event_name: str, **kwargs):
    """
    Logs structured data as space-separated key=value pairs.
    Example: log_event(logger, 'investigation_started', case_id='case_123', worker_id='worker_02')
    -> INFO investigation_started case_id=case_123 worker_id=worker_02
    """
    kv_pairs = " ".join([f"{k}={v}" for k, v in kwargs.items()])
    logger.info(f"{event_name} {kv_pairs}".strip())
