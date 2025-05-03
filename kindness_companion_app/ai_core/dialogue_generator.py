import logging
from .api_client import get_api_key, make_api_request
from requests.exceptions import RequestException

logger = logging.getLogger(__name__)
ZHIPUAI_API_ENDPOINT = "https://open.bigmodel.cn/api/paas/v4/chat/completions" # Common endpoint
DEFAULT_MODEL = "glm-4-flash" # Or another suitable model

def generate_pet_dialogue(user_id: int, event_type: str, event_data: dict) -> str:
    """Generates pet dialogue based on user events using an AI API."""
    # 1. Construct a prompt based on the event
    #    (This needs more sophisticated logic based on event_type and event_data)
    #    Improved prompt construction:
    prompt_parts = [f"You are a friendly and encouraging virtual pet in the Kindness Companion app."]
    prompt_parts.append(f"A user (ID: {user_id}) just triggered an event: '{event_type}'.")

    if event_type == 'check_in' and 'challenge_title' in event_data:
        prompt_parts.append(f"They checked in for the challenge: '{event_data['challenge_title']}'.")
    elif event_type == 'reflection_added':
        if 'text' in event_data and event_data['text']:
            prompt_parts.append(f"They added a reflection: \"{event_data['text']}\".")
        if 'analyzed_emotion' in event_data:
             prompt_parts.append(f"The reflection seems '{event_data['analyzed_emotion']}'.")
    elif event_type == 'user_message':
        if 'message' in event_data and event_data['message']:
            prompt_parts.append(f"They sent you a direct message: \"{event_data['message']}\".")
            prompt_parts.append("Please respond to their message in a friendly, helpful way.")
        if 'analyzed_emotion' in event_data:
            prompt_parts.append(f"The message seems '{event_data['analyzed_emotion']}'.")
    # Add more context based on other event types if needed

    prompt_parts.append("Generate a short, warm, and encouraging response (in Chinese) suitable for a virtual pet.")
    prompt = " ".join(prompt_parts)

    logger.info(f"Generating dialogue for user {user_id}, event: {event_type}")

    # 2. Call the dialogue API
    try:
        response_text = _call_dialogue_api(prompt)
        if not response_text:
            logger.warning("Dialogue API returned empty response.")
            return "... (宠物似乎正在安静地思考)" # More user-friendly default
        return response_text
    except Exception as e:
        logger.error(f"Error generating dialogue: {e}")
        return "... (宠物好像在想些什么)" # More user-friendly error

def _call_dialogue_api(prompt: str) -> str | None:
    """
    Private helper function to call the configured dialogue generation API (ZhipuAI).
    Requires API key management (from config.py via api_client).
    """
    api_key = get_api_key('ZHIPUAI')
    if not api_key:
        logger.error("ZhipuAI API key not found. Cannot call dialogue API.")
        return None

    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }

    # Construct the payload according to ZhipuAI API V4
    payload = {
        "model": DEFAULT_MODEL,
        "messages": [
            # System prompt is now part of the main prompt for better context control
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 60, # Slightly increased token limit for potentially richer responses
        "temperature": 0.8 # Adjust creativity
    }

    try:
        logger.debug(f"Calling ZhipuAI Dialogue API. Endpoint: {ZHIPUAI_API_ENDPOINT}, Model: {DEFAULT_MODEL}")
        # Use make_api_request from api_client
        response_data = make_api_request(
            method='POST',
            url=ZHIPUAI_API_ENDPOINT,
            headers=headers,
            json_data=payload
        )

        # Extract the response text (structure depends on API V4)
        if response_data and 'choices' in response_data and response_data['choices']:
            # Check if message is a dict and has content
            message = response_data['choices'][0].get('message')
            if isinstance(message, dict) and 'content' in message:
                dialogue = message['content'].strip()
                # Basic check for empty or placeholder responses from the API itself
                if dialogue and dialogue != "[empty]" and dialogue != "[blank]":
                    logger.info(f"Received dialogue from API: {dialogue[:50]}...")
                    return dialogue
                else:
                    logger.warning(f"ZhipuAI API returned an empty or placeholder dialogue: '{dialogue}'")
                    return None
            else:
                logger.warning(f"Unexpected response structure from ZhipuAI API: 'message' object is not a dict or missing 'content'. Message: {message}. Response: {response_data}")
                return None
        else:
            logger.warning(f"Unexpected response structure or empty choices from ZhipuAI API: {response_data}")
            return None

    except RequestException as e:
        logger.error(f"ZhipuAI API request failed: {e}")
        return None
    except Exception as e:
        # Log the full traceback for unexpected errors
        logger.error(f"An unexpected error occurred calling ZhipuAI API: {e}", exc_info=True)
        return None
