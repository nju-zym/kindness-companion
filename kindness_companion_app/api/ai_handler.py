"""
Handles interactions with external AI APIs, like ZhipuAI.
"""

import logging
from typing import Optional, List, Dict, Any
from zhipuai import ZhipuAI

# Attempt to import the API key from config
try:
    from ..config import ZHIPUAI_API_KEY
except ImportError:
    logging.error(
        "Failed to import ZHIPUAI_API_KEY from config.py. Make sure the file exists and the variable is set."
    )
    ZHIPUAI_API_KEY = None

logger = logging.getLogger(__name__)


def get_zhipuai_completion(
    messages: List[Dict[str, str]], model: str = "glm-4-flash-250414"
) -> Optional[str]:
    """
    Gets a completion from the ZhipuAI API.

    Args:
        messages (list): A list of message dictionaries (e.g., [{'role': 'user', 'content': 'Hello'}]).
        model (str): The ZhipuAI model to use (default: 'glm-4-flash-250414').

    Returns:
        str: The content of the assistant's response, or None if an error occurs or API key is missing.
    """
    if not ZHIPUAI_API_KEY or ZHIPUAI_API_KEY == "YOUR_ZHIPUAI_API_KEY":
        logger.error("ZhipuAI API key is not configured in config.py.")
        return None

    try:
        client = ZhipuAI(api_key=ZHIPUAI_API_KEY)
        response: Any = client.chat.completions.create(
            model=model,
            messages=messages,
        )
        logger.info(f"ZhipuAI API call successful. Model: {model}")
        # Get the assistant's response content from the response object
        if response and hasattr(response, "choices") and response.choices:
            return response.choices[0].message.content
        else:
            logger.warning(f"ZhipuAI response structure unexpected: {response}")
            return None
    except Exception as e:
        logger.error(f"Error calling ZhipuAI API: {e}")
        return None
