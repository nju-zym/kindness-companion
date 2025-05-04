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

def _call_emotion_api(text: str) -> str | None:
    """
    Calls the ZhipuAI API to analyze emotion.
    """
    api_key = get_api_key()
    if not api_key:
        logger.error("ZhipuAI API key not configured.")
        return None

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    # Simple, direct prompt for classification
    prompt = f"""Analyze the predominant emotion of the following text. Classify it strictly as one of: 'positive', 'negative', or 'neutral'.

Text: "{text}"

Classification:""" # Added a label to guide the model

    payload = {
        "model": DEFAULT_MODEL,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 10, # Allow a bit more room just in case, but expect short response
        "temperature": 0.1 # Low temperature for deterministic classification
    }

    try:
        response_json = make_api_request(ZHIPUAI_API_ENDPOINT, headers=headers, json_payload=payload)
        if response_json:
            # Extract the classification, expecting it directly
            classification = response_json.get("choices", [{}])[0].get("message", {}).get("content", "").strip().lower()
            # Validate the output
            if classification in ['positive', 'negative', 'neutral']:
                logger.info(f"Emotion analysis result: {classification}")
                return classification
            else:
                logger.warning(f"Unexpected emotion analysis result format: {classification}")
                # Attempt to find the keyword if the model added extra text
                if 'positive' in classification: return 'positive'
                if 'negative' in classification: return 'negative'
                if 'neutral' in classification: return 'neutral'
                return None # Could not reliably parse
        else:
            return None
    except RequestException as e:
        logger.error(f"API request failed during emotion analysis: {e}")
        return None
    except (KeyError, IndexError, AttributeError) as e:
        logger.error(f"Error parsing emotion analysis API response: {e}")
        return None
