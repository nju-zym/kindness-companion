import logging
from typing import Optional, Dict, Tuple
from .api_client import get_api_key, make_api_request
from requests.exceptions import RequestException

logger = logging.getLogger(__name__)
ZHIPUAI_API_ENDPOINT = "https://open.bigmodel.cn/api/paas/v4/chat/completions" # Reusing the chat endpoint
DEFAULT_MODEL = "glm-4-flash" # Or a model suitable for classification

# Define emotion categories and corresponding animations
EMOTION_CATEGORIES = {
    # Basic emotions
    'happy': 'happy',
    'excited': 'excited',
    'joyful': 'excited',
    'content': 'happy',
    'proud': 'excited',
    'grateful': 'happy',
    'optimistic': 'happy',

    # Negative emotions
    'sad': 'concerned',
    'anxious': 'concerned',
    'worried': 'concerned',
    'frustrated': 'concerned',
    'angry': 'concerned',
    'disappointed': 'concerned',
    'stressed': 'concerned',

    # Neutral emotions
    'neutral': 'idle',
    'calm': 'idle',
    'reflective': 'idle',
    'curious': 'idle',
    'surprised': 'confused',
    'confused': 'confused',
    'uncertain': 'confused',

    # Fallback categories
    'positive': 'happy',
    'negative': 'concerned',
}

def analyze_emotion_for_pet(user_id: int, reflection_text: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Analyzes the emotion of the user's reflection text using an AI API.
    Returns a tuple of (emotion_category, suggested_animation).

    Args:
        user_id: The ID of the user
        reflection_text: The text to analyze

    Returns:
        Tuple of (emotion_category, suggested_animation)
        emotion_category is a detailed emotion (e.g., 'happy', 'sad', 'anxious')
        suggested_animation is the animation name to display (e.g., 'happy', 'concerned', 'confused')
    """
    if not reflection_text:
        logger.warning(f"Cannot analyze empty reflection text for user {user_id}.")
        return None, None

    logger.info(f"Analyzing emotion for user {user_id}'s reflection.")
    try:
        emotion = _call_detailed_emotion_api(reflection_text)
        if emotion:
            logger.info(f"Detected detailed emotion: {emotion}")
            # Get corresponding animation
            animation = EMOTION_CATEGORIES.get(emotion.lower(), 'idle')
            return emotion, animation
        else:
            logger.warning("Emotion analysis API returned no result.")
            # Fallback to basic emotion analysis
            basic_emotion = _call_basic_emotion_api(reflection_text)
            if basic_emotion:
                logger.info(f"Detected basic emotion: {basic_emotion}")
                animation = 'happy' if basic_emotion == 'positive' else 'concerned' if basic_emotion == 'negative' else 'idle'
                return basic_emotion, animation
            return None, None
    except Exception as e:
        logger.error(f"Error during emotion analysis: {e}")
        return None, None # Indicate failure

def _call_detailed_emotion_api(text: str) -> Optional[str]:
    """
    Calls the ZhipuAI API to analyze detailed emotion.
    Returns a specific emotion category.
    """
    api_key = get_api_key('ZHIPUAI')
    if not api_key:
        logger.error("ZhipuAI API key not configured.")
        return None

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    # Detailed emotion analysis prompt
    prompt = f"""分析以下文本中表达的主要情绪。从以下情绪类别中选择一个最匹配的：
- 快乐(happy)
- 兴奋(excited)
- 欣喜(joyful)
- 满足(content)
- 自豪(proud)
- 感激(grateful)
- 乐观(optimistic)
- 悲伤(sad)
- 焦虑(anxious)
- 担忧(worried)
- 沮丧(frustrated)
- 愤怒(angry)
- 失望(disappointed)
- 压力(stressed)
- 平静(calm)
- 思考(reflective)
- 好奇(curious)
- 惊讶(surprised)
- 困惑(confused)
- 不确定(uncertain)
- 中性(neutral)

文本: "{text}"

只返回一个情绪类别，不要添加任何解释。"""

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

            # Clean up the response - extract just the emotion word
            for emotion in EMOTION_CATEGORIES.keys():
                if emotion in classification:
                    return emotion

            # If no match found, return the raw classification
            logger.warning(f"Unexpected emotion format: {classification}")
            return classification if classification else None
        else:
            return None
    except RequestException as e:
        logger.error(f"API request failed during detailed emotion analysis: {e}")
        return None
    except (KeyError, IndexError, AttributeError) as e:
        logger.error(f"Error parsing detailed emotion analysis API response: {e}")
        return None

def _call_basic_emotion_api(text: str) -> Optional[str]:
    """
    Calls the ZhipuAI API to analyze basic emotion.
    Returns a simple emotion category (e.g., 'positive', 'negative', 'neutral').
    """
    api_key = get_api_key('ZHIPUAI')
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
                logger.info(f"Basic emotion analysis result: {classification}")
                return classification
            else:
                logger.warning(f"Unexpected basic emotion analysis result format: {classification}")
                # Attempt to find the keyword if the model added extra text
                if 'positive' in classification: return 'positive'
                if 'negative' in classification: return 'negative'
                if 'neutral' in classification: return 'neutral'
                return None # Could not reliably parse
        else:
            return None
    except RequestException as e:
        logger.error(f"API request failed during basic emotion analysis: {e}")
        return None
    except (KeyError, IndexError, AttributeError) as e:
        logger.error(f"Error parsing basic emotion analysis API response: {e}")
        return None
