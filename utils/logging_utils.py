import logging
import sys

def setup_logging(level=logging.INFO):
    """Set up logging for the project."""
    logging.basicConfig(
        stream=sys.stdout,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        level=level,
    )
