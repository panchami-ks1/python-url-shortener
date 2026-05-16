import logging
import sys

def setup_logger():
    logger = logging.getLogger("url_shortener")
    logger.setLevel(logging.INFO)
    
    # Avoid adding multiple handlers if logger is imported multiple times
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
    return logger

logger = setup_logger()
