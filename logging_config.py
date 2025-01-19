"""
This module configures logging settings for the application.
It sets up the logging format and logging level for the application.

Logging is configured to display the timestamp, logger name, log level, and message.
"""
import logging

# Log configuration
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)
