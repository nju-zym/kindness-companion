import requests
from requests.exceptions import RequestException
import time
import logging
from typing import Optional, Dict, Any

# Attempt to import the config module directly (absolute import)
try:
    import config
except ImportError:
    logging.warning("Could not import config.py. API keys might not be available.")
    config = None  # type: ignore

DEFAULT_TIMEOUT = 15  # seconds
MAX_RETRIES = 3
BACKOFF_FACTOR = 0.5  # seconds

logger = logging.getLogger(__name__)


def make_api_request(
    url: str,
    method: str = "POST",
    headers: Optional[Dict[str, str]] = None,
    data: Optional[Dict[str, Any]] = None,
    timeout: int = 30,
) -> Optional[Dict[str, Any]]:
    """
    Make an API request to the specified endpoint.

    Args:
        url: API endpoint URL
        method: HTTP method (default: POST)
        headers: Request headers
        data: Request payload
        timeout: Request timeout in seconds

    Returns:
        Response data as dictionary or None if request fails
    """
    try:
        response = requests.request(
            method=method, url=url, headers=headers, json=data, timeout=timeout
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {str(e)}")
        return None


def get_api_key(service_name: str) -> str | None:
    """
    Securely retrieves the API key for a given service from config.py.

    Args:
        service_name: The name of the service (e.g., 'ZHIPUAI').
                      The function will look for a variable named
                      f'{service_name.upper()}_API_KEY' in config.py.

    Returns:
        The API key string if found, otherwise None.
    """
    if not config:
        logger.error("Config module not loaded. Cannot retrieve API key.")
        return None

    key_variable_name = f"{service_name.upper()}_API_KEY"
    api_key = getattr(config, key_variable_name, None)

    if not api_key:
        logger.warning(f"API key '{key_variable_name}' not found in config.py.")
        return None

    logger.info(f"Retrieved API key for {service_name}.")
    return api_key
