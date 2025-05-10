import logging
from typing import Optional, Dict, Tuple, List, Callable
import os
import requests
from requests.exceptions import RequestException
import threading
import queue
import time

logger = logging.getLogger(__name__)

# API configuration
ZHIPUAI_API_ENDPOINT = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
DEFAULT_MODEL = "glm-4-flash"

# Animation states
ANIMATION_STATES = {
    "thinking": "thinking",
    "idle": "idle",
    "happy": "happy",
    "concerned": "concerned",
    "confused": "confused",
    "excited": "excited",
}

# Detailed emotion categories and their corresponding animations
EMOTION_CATEGORIES: Dict[str, str] = {
    # Positive emotions
    "happy": "happy",
    "excited": "excited",
    "joyful": "excited",
    "proud": "excited",
    "grateful": "happy",
    "content": "happy",
    "optimistic": "happy",
    "cheerful": "happy",
    "delighted": "excited",
    "enthusiastic": "excited",
    # Negative emotions
    "sad": "concerned",
    "anxious": "concerned",
    "worried": "concerned",
    "frustrated": "concerned",
    "angry": "concerned",
    "disappointed": "concerned",
    "stressed": "concerned",
    "tired": "concerned",
    "overwhelmed": "concerned",
    "lonely": "concerned",
    # Neutral/Complex emotions
    "surprised": "confused",
    "confused": "confused",
    "uncertain": "confused",
    "curious": "idle",
    "thoughtful": "idle",
    "reflective": "idle",
    "calm": "idle",
    "peaceful": "idle",
    "neutral": "idle",
    # Basic emotions (fallback)
    "positive": "happy",
    "negative": "concerned",
    "neutral": "idle",
}

# Valid basic emotions for fallback analysis
BASIC_EMOTIONS: List[str] = ["positive", "negative", "neutral"]

# Keywords for emotion detection when API fails
EMOTION_KEYWORDS: Dict[str, List[str]] = {
    "sad": [
        "难过",
        "伤心",
        "悲伤",
        "不开心",
        "沮丧",
        "失望",
        "痛苦",
        "生病",
        "难受",
        "不舒服",
        "不适",
        "累",
        "疲惫",
    ],
    "angry": ["生气", "愤怒", "恼火", "烦躁", "不满", "不爽"],
    "anxious": ["焦虑", "担心", "紧张", "不安", "害怕", "恐惧"],
    "happy": ["开心", "高兴", "快乐", "愉快", "兴奋", "喜悦", "棒", "赞"],
    "neutral": ["一般", "还行", "还好", "普通"],
}

# Negative modifiers that invert the emotion
NEGATIVE_MODIFIERS: List[str] = [
    "不",
    "没",
    "别",
    "不要",
    "不能",
    "不会",
    "没有",
    "不是",
]


def get_api_key(service: str) -> Optional[str]:
    """Get API key from environment variables."""
    return os.getenv(f"{service}_API_KEY")


def _call_ai_api(
    prompt: str,
    system_prompt: Optional[str] = None,
    status_queue: Optional[queue.Queue] = None,
) -> Optional[str]:
    """
    Makes a call to the AI API for emotion analysis.

    Args:
        prompt: The prompt to send to the API
        system_prompt: Optional system prompt to guide the model
        status_queue: Optional queue to report status updates

    Returns:
        The API response text, or None if the call fails
    """
    try:
        api_key = get_api_key("ZHIPUAI")
        if not api_key:
            logger.error("ZhipuAI API key not configured.")
            if status_queue:
                # Don't put error message in status queue, just log it
                logger.warning(
                    "API key not configured, falling back to keyword detection"
                )
            return None

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": DEFAULT_MODEL,
            "messages": messages,
            "max_tokens": 10,
            "temperature": 0.1,
        }

        # Make the API call with a timeout
        response = requests.post(
            ZHIPUAI_API_ENDPOINT, headers=headers, json=payload, timeout=2
        )
        response.raise_for_status()
        response_json = response.json()

        if response_json and "choices" in response_json and response_json["choices"]:
            result = (
                response_json["choices"][0]
                .get("message", {})
                .get("content", "")
                .strip()
            )
            return result

        return None
    except requests.Timeout:
        logger.error("API request timed out")
        return None
    except RequestException as e:
        logger.error(f"API request failed: {e}")
        return None
    except (KeyError, IndexError, AttributeError) as e:
        logger.error(f"Error parsing API response: {e}")
        return None


def _detect_emotion_from_keywords(text: str) -> Optional[str]:
    text = text.lower()
    # 优先检测负面情绪
    for emotion in ["sad", "angry", "anxious"]:
        for keyword in EMOTION_KEYWORDS[emotion]:
            if keyword in text:
                return emotion
    # 再检测正面
    for keyword in EMOTION_KEYWORDS["happy"]:
        if keyword in text:
            return "happy"
    for keyword in EMOTION_KEYWORDS["neutral"]:
        if keyword in text:
            return "neutral"
    return None


def _call_detailed_emotion_api(
    text: str, status_queue: Optional[queue.Queue] = None
) -> Optional[str]:
    """
    Calls the AI API to analyze detailed emotions in the text.
    Returns a specific emotion category from EMOTION_CATEGORIES.
    """
    try:
        system_prompt = """你是一个专业的情绪分析助手。你的任务是分析文本中的情绪，并返回最匹配的情绪类别。
        请只返回以下情绪类别之一：happy, sad, angry, anxious, surprised, confused, neutral。
        不要添加任何解释或其他文字。"""

        prompt = f"""分析这段文本的情绪：
        "{text}"
        
        只返回一个情绪类别：happy, sad, angry, anxious, surprised, confused, neutral"""

        response = _call_ai_api(prompt, system_prompt, status_queue)
        if response:
            emotion = response.lower().strip()
            if emotion in EMOTION_CATEGORIES:
                logger.info(f"AI detected emotion: {emotion}")
                return emotion
            logger.warning(f"AI returned unrecognized emotion: {emotion}")
        return None
    except Exception as e:
        logger.error(f"Error in detailed emotion analysis: {e}")
        return None


def _call_basic_emotion_api(text: str) -> Optional[str]:
    """
    Fallback function for basic emotion analysis (positive/negative/neutral).
    """
    try:
        prompt = f"""Analyze if this text has a positive, negative, or neutral emotional tone.
        
        Text: "{text}"
        
        Return only one word: 'positive', 'negative', or 'neutral'."""

        response = _call_ai_api(prompt)
        if response:
            emotion = response.lower()
            if emotion in BASIC_EMOTIONS:
                return emotion
        return None
    except Exception as e:
        logger.error(f"Error in basic emotion analysis: {e}")
        return None


def test_emotion_analysis():
    """Test function to verify emotion analysis functionality"""
    test_cases = [
        "我很开心",
        "我很难过",
        "我很生气",
        "我很焦虑",
        "我很惊讶",
        "我很困惑",
        "我很累",
        "我很兴奋",
    ]

    def status_callback(status: str):
        print(f"Status update: {status}")
        # Verify that thinking animation is shown immediately
        if status == ANIMATION_STATES["thinking"]:
            print("✓ Thinking animation shown immediately")

    for test_text in test_cases:
        print(f"\nTesting with text: {test_text}")
        emotion, animation = analyze_emotion_for_pet(1, test_text, status_callback)
        print(f"Result - Emotion: {emotion}, Animation: {animation}")
        time.sleep(1)  # Wait between tests


def analyze_emotion_for_pet(
    user_id: int,
    reflection_text: str,
    status_callback: Optional[Callable[[str], None]] = None,
) -> Tuple[Optional[str], Optional[str]]:
    """
    优先用AI分析情绪，AI失败时用关键词兜底，保证thinking动画立即切换。
    """
    if not reflection_text:
        logger.warning(f"Cannot analyze empty reflection text for user {user_id}.")
        if status_callback:
            status_callback(ANIMATION_STATES["idle"])
        return None, ANIMATION_STATES["idle"]

    # 立即切换到thinking动画
    if status_callback:
        status_callback(ANIMATION_STATES["thinking"])

    logger.info(f"Analyzing emotion for user {user_id}'s reflection.")

    result_queue = queue.Queue()
    status_queue = queue.Queue()

    def status_updater():
        try:
            while True:
                try:
                    status = status_queue.get(timeout=0.1)
                    if status == "STOP":
                        break
                    if status_callback:
                        logger.debug(f"Updating status to: {status}")
                        status_callback(status)
                except queue.Empty:
                    continue
        except Exception as e:
            logger.error(f"Error in status updater: {e}")

    def analyze_thread():
        try:
            # 优先AI分析
            emotion = _call_detailed_emotion_api(reflection_text, status_queue)
            if emotion:
                logger.info(f"AI detected emotion: {emotion}")
                animation = EMOTION_CATEGORIES.get(
                    emotion.lower(), ANIMATION_STATES["idle"]
                )
                result_queue.put((emotion, animation))
                return
            # AI失败再用关键词兜底
            logger.info("AI analysis failed, trying keyword-based detection...")
            keyword_emotion = _detect_emotion_from_keywords(reflection_text)
            if keyword_emotion:
                logger.info(f"Detected emotion from keywords: {keyword_emotion}")
                animation = EMOTION_CATEGORIES.get(
                    keyword_emotion.lower(), ANIMATION_STATES["idle"]
                )
                result_queue.put((keyword_emotion, animation))
                return
            logger.warning(
                "All emotion analysis methods failed, defaulting to concerned animation"
            )
            result_queue.put((None, ANIMATION_STATES["concerned"]))
        except Exception as e:
            logger.error(f"Error during emotion analysis: {e}")
            result_queue.put((None, ANIMATION_STATES["concerned"]))
        finally:
            status_queue.put("STOP")

    # 启动状态线程
    status_thread = threading.Thread(target=status_updater)
    status_thread.daemon = True
    status_thread.start()
    # 启动分析线程
    analysis_thread = threading.Thread(target=analyze_thread)
    analysis_thread.daemon = True
    analysis_thread.start()
    try:
        emotion, animation = result_queue.get(timeout=3)
        logger.debug(f"Analysis complete. Emotion: {emotion}, Animation: {animation}")
        return emotion, animation
    except queue.Empty:
        logger.error("Emotion analysis timed out")
        return None, ANIMATION_STATES["concerned"]


if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.DEBUG)

    # Run tests
    print("Starting emotion analysis tests...")
    test_emotion_analysis()
    print("\nTests completed.")
