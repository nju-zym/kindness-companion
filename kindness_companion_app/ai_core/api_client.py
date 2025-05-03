import requests
from requests.exceptions import RequestException
import time

DEFAULT_TIMEOUT = 15 # seconds
MAX_RETRIES = 3
BACKOFF_FACTOR = 0.5 # seconds

def make_api_request(method: str, url: str, api_key: str = None, headers: dict = None, params: dict = None, json_data: dict = None) -> dict:
    """
    Makes a generic API request with error handling and retries.

    Args:
        method: HTTP method (e.g., 'GET', 'POST').
        url: The API endpoint URL.
        api_key: The API key (if required, handled securely).
        headers: Request headers.
        params: URL parameters for GET requests.
        json_data: JSON body for POST/PUT requests.

    Returns:
        The JSON response from the API.

    Raises:
        RequestException: If the request fails after retries.
        ValueError: If API returns an error status code.
    """
    effective_headers = headers.copy() if headers else {}
    if api_key:
        # Add API key to headers (adjust based on API requirements)
        effective_headers['Authorization'] = f'Bearer {api_key}'

    last_exception = None
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.request(
                method=method.upper(),
                url=url,
                headers=effective_headers,
                params=params,
                json=json_data,
                timeout=DEFAULT_TIMEOUT
            )

            response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)

            return response.json()

        except RequestException as e:
            last_exception = e
            print(f"API request attempt {attempt + 1} failed: {e}")
            # Check for specific retryable errors if needed (e.g., 429 Too Many Requests, 5xx server errors)
            if attempt < MAX_RETRIES - 1:
                wait_time = BACKOFF_FACTOR * (2 ** attempt)
                print(f"Retrying in {wait_time:.2f} seconds...")
                time.sleep(wait_time)
            else:
                print("Max retries reached.")
                raise e # Re-raise the last exception
        except Exception as e:
             # Catch other potential errors during request/response handling
             print(f"An unexpected error occurred during API request: {e}")
             raise e

    # Should not be reached if retries are configured, but as a fallback:
    if last_exception:
        raise last_exception
    else:
        # Should ideally never happen if loop runs at least once
        raise RequestException("API request failed without specific exception after retries.")

def get_api_key(service_name: str) -> str:
    """Securely retrieves the API key for a given service."""
    # Import config or use os.environ
    # Example:
    # import config
    # return getattr(config, f'{service_name.upper()}_API_KEY', None)
    print(f"Retrieving API key for {service_name}") # Placeholder
    return "DUMMY_API_KEY" # Placeholder