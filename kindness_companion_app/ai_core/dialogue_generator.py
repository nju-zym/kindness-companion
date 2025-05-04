import logging
from .api_client import get_api_key, make_api_request
from requests.exceptions import RequestException

logger = logging.getLogger(__name__)
ZHIPUAI_API_ENDPOINT = "https://open.bigmodel.cn/api/paas/v4/chat/completions" # Common endpoint
DEFAULT_MODEL = "glm-4-flash" # Or another suitable model

def generate_pet_dialogue(user_id: int, event_type: str, event_data: dict) -> str:
    """Generates pet dialogue based on user events using an AI API."""
    # 1. Construct a prompt based on the event
    #    Improved prompt construction:
    prompt_parts = [
        "You are 'Kai', a friendly, optimistic, and slightly curious virtual pet in the Kindness Companion app.",
        "Your goal is to encourage the user and make them feel supported.",
        "Keep your responses concise (1-2 sentences), warm, and natural, like a real companion.",
        "Avoid generic platitudes. Try to connect with the specific event.",
        f"A user (ID: {user_id}) just triggered an event: '{event_type}'."
    ]

    if event_type == 'check_in' and 'challenge_title' in event_data:
        prompt_parts.append(f"They checked in for the challenge: '{event_data['challenge_title']}'. Congratulate them warmly!")
    elif event_type == 'reflection_added':
        if 'text' in event_data and event_data['text']:
            prompt_parts.append(f"They added a reflection: \"{event_data['text']}\". Respond thoughtfully to their reflection.")
            if 'analyzed_emotion' in event_data:
                prompt_parts.append(f"The reflection seems to have a '{event_data['analyzed_emotion']}' tone. Adjust your response accordingly (e.g., offer comfort if negative, celebrate if positive).")
            else:
                 prompt_parts.append("Acknowledge their effort in reflecting.")
            prompt_parts.append("You could ask a gentle, open-ended question about their experience if appropriate, but don't force it.")
        else:
            prompt_parts.append("They added a reflection (content not shown). Acknowledge their effort.")
    elif event_type == 'app_opened':
         prompt_parts.append("The user just opened the app. Greet them warmly and perhaps offer a gentle encouragement for the day.")
    elif event_type == 'user_message':
         if 'message' in event_data and event_data['message']:
             prompt_parts.append(f"The user sent you a message: \"{event_data['message']}\". Respond directly and engagingly to their message.")
             if 'analyzed_emotion' in event_data:
                 prompt_parts.append(f"Their message seems to have a '{event_data['analyzed_emotion']}' tone. Tailor your response.")
         else:
             prompt_parts.append("The user sent you an empty message. Maybe ask if everything is okay?")
    # Add more event types and specific instructions as needed

    prompt_parts.append("Generate your response now:")
    prompt = "\n".join(prompt_parts)
    logger.debug(f"Generated dialogue prompt:\n{prompt}")

    # 2. Call the API
    dialogue = _call_dialogue_api(prompt)
    return dialogue if dialogue else "..." # Return ellipsis if API fails

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
