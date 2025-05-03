import logging
from typing import Optional, Dict
from .api_client import get_api_key, make_api_request
from requests.exceptions import RequestException

logger = logging.getLogger(__name__)
ZHIPUAI_API_ENDPOINT = "https://open.bigmodel.cn/api/paas/v4/chat/completions" # Reusing the chat endpoint
DEFAULT_MODEL = "glm-4-flash" # Or a model suitable for classification

def analyze_emotion_for_pet(user_id: int, reflection_text: str) -> Optional[str]:
    """
    Analyzes the emotion of the user's reflection text using an AI API.
    Returns a simple emotion category (e.g., 'positive', 'negative', 'neutral').
    """
    if not reflection_text:
        logger.warning(f"Cannot analyze empty reflection text for user {user_id}.")
        return None

    logger.info(f"Analyzing emotion for user {user_id}'s reflection.")
    try:
        emotion = _call_emotion_api(reflection_text)
        if emotion:
            logger.info(f"Detected emotion: {emotion}")
        else:
            logger.warning("Emotion analysis API returned no result.")
        return emotion
    except Exception as e:
        logger.error(f"Error analyzing emotion: {e}")
        return None # Indicate failure

def _call_emotion_api(text: str) -> Optional[str]:
    """
    Private helper function to call the configured emotion analysis API (using ZhipuAI Chat).
    Requires API key management.
    """
    api_key = get_api_key('ZHIPUAI')
    if not api_key:
        logger.error("ZhipuAI API key not found. Cannot call emotion analysis API.")
        return None

    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }

    # Craft a prompt specifically for emotion classification
    prompt = f"Analyze the emotion of the following text and return only one word: 'positive', 'negative', or 'neutral'. Text: \"{text}\""

    payload = {
        "model": DEFAULT_MODEL,
        "messages": [
            {"role": "system", "content": "You are an emotion analysis assistant. Respond with only one word: positive, negative, or neutral."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 5, # Very short response expected
        "temperature": 0.1 # Low temperature for classification task
    }

    try:
        logger.debug(f"Calling ZhipuAI Emotion Analysis (Chat) API. Model: {DEFAULT_MODEL}")
        response_data = make_api_request(
            method='POST',
            url=ZHIPUAI_API_ENDPOINT,
            headers=headers,
            json_data=payload
        )

        # Extract the response text
        if response_data and 'choices' in response_data and response_data['choices']:
            message = response_data['choices'][0].get('message')
            if message and 'content' in message:
                emotion_result = message['content'].strip().lower()
                # Validate the result
                if emotion_result in ['positive', 'negative', 'neutral']:
                    logger.info(f"Received emotion analysis result: {emotion_result}")
                    return emotion_result
                else:
                    logger.warning(f"Unexpected emotion analysis result from API: '{emotion_result}'. Response: {response_data}")
                    return None # Or maybe default to neutral?
            else:
                logger.warning(f"Unexpected response structure from ZhipuAI API (Emotion): No message content. Response: {response_data}")
                return None
        else:
            logger.warning(f"Unexpected response structure or empty choices from ZhipuAI API (Emotion): {response_data}")
            return None

    except RequestException as e:
        logger.error(f"ZhipuAI API request failed (Emotion): {e}")
        return None
    except Exception as e:
        logger.error(f"An unexpected error occurred calling ZhipuAI API (Emotion): {e}")
        return None
