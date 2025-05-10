import logging
import datetime
from typing import Dict, Any, Callable, Optional
from functools import lru_cache
import time
from .api_client import get_api_key, make_api_request
from requests.exceptions import RequestException

logger = logging.getLogger(__name__)
ZHIPUAI_API_ENDPOINT = (
    "https://open.bigmodel.cn/api/paas/v4/chat/completions"  # Reusing chat endpoint
)
DEFAULT_MODEL = "glm-4-flash"  # Or a model suitable for summarization/reporting

# Constants for retry mechanism
MAX_RETRIES = 3
RETRY_DELAY = 1  # seconds
CACHE_TTL = 3600  # 1 hour in seconds


class ReportGenerationError(Exception):
    """Base exception for report generation errors."""

    pass


class DataFetchError(ReportGenerationError):
    """Exception raised when there's an error fetching user data."""

    pass


class APIError(ReportGenerationError):
    """Exception raised when there's an error with the API call."""

    pass


class ValidationError(ReportGenerationError):
    """Exception raised when data validation fails."""

    pass


def validate_user_data(data: Dict[str, Any]) -> bool:
    """
    Validates the user data for report generation.

    Args:
        data: The user data to validate

    Returns:
        bool: True if data is valid, False otherwise

    Raises:
        ValidationError: If data validation fails
    """
    if not isinstance(data, dict):
        raise ValidationError("User data must be a dictionary")

    required_fields = [
        "check_ins",
        "streak",
        "reflections",
        "top_category",
        "new_achievements",
    ]
    for field in required_fields:
        if field not in data:
            raise ValidationError(f"Missing required field: {field}")

    if not isinstance(data["check_ins"], int) or data["check_ins"] < 0:
        raise ValidationError("check_ins must be a non-negative integer")

    if not isinstance(data["streak"], int) or data["streak"] < 0:
        raise ValidationError("streak must be a non-negative integer")

    if not isinstance(data["reflections"], int) or data["reflections"] < 0:
        raise ValidationError("reflections must be a non-negative integer")

    if not isinstance(data["top_category"], str):
        raise ValidationError("top_category must be a string")

    if not isinstance(data["new_achievements"], list):
        raise ValidationError("new_achievements must be a list")

    return True


def _get_cache_key(user_id: int, start_date: str, end_date: str) -> str:
    """Generate a cache key for the report."""
    return f"{user_id}_{start_date}_{end_date}"


def generate_weekly_report(report_input: Dict[str, Any]) -> str:
    """
    Generates a personalized weekly kindness report for the user using an AI API.
    Includes retry mechanism and caching.

    Args:
        report_input: A dictionary containing user data and report parameters.

    Returns:
        A string containing the generated report text, or an error message if generation fails.

    Raises:
        ReportGenerationError: If report generation fails
    """
    user_id = report_input.get("user_id")
    if not user_id:
        return "生成报告时出错：缺少用户ID"

    logger.info(f"Generating weekly report for user {user_id}.")

    # 1. Fetch user data for the report period
    try:
        user_data = _get_user_data_for_report(user_id)
        if not user_data:
            raise DataFetchError("No user data found")

        # Validate user data
        validate_user_data(user_data)

        if user_data.get("check_ins", 0) == 0 and user_data.get("streak", 0) == 0:
            return "无法生成报告，似乎还没有足够的活动数据。请先完成一些善行伴侣后再尝试生成报告。"

    except ValidationError as e:
        logger.error(f"Data validation error: {e}")
        return f"生成报告时出错（数据验证失败）：{str(e)}"
    except DataFetchError as e:
        logger.error(f"Error fetching user data: {e}")
        return f"生成报告时出错（获取数据失败）：{str(e)}"
    except Exception as e:
        logger.error(f"Unexpected error fetching user data: {e}")
        return "生成报告时出错（未知错误）。请稍后再试或联系支持团队。"

    # 2. Get additional context for a more personalized report
    try:
        additional_context = _get_additional_context(user_id, user_data)
    except Exception as e:
        logger.warning(
            f"Error getting additional context: {e}. Will proceed with basic report."
        )
        additional_context = {}

    # 3. Construct a prompt for the text generation API
    prompt = _build_report_prompt(user_id, user_data, additional_context)

    # 4. Call the text generation API with retry mechanism
    for attempt in range(MAX_RETRIES):
        try:
            report_text = _call_text_generation_api(prompt)
            if not report_text:
                raise APIError("Empty response from API")

            # Post-process the report text
            report_text = _post_process_report(report_text)

            logger.info(
                f"Generated report text (first 50 chars): {report_text[:50]}..."
            )
            return report_text

        except APIError as e:
            if attempt == MAX_RETRIES - 1:
                logger.error(f"API error after {MAX_RETRIES} attempts: {e}")
                return "生成报告时与 AI 连接出现问题。请检查网络连接或稍后再试。"
            logger.warning(f"API error (attempt {attempt + 1}/{MAX_RETRIES}): {e}")
            time.sleep(RETRY_DELAY)
        except Exception as e:
            logger.error(f"Unexpected error calling API: {e}")
            return "生成报告时出现未知错误。请稍后再试。"

    # This should never be reached due to the return statements in the loop,
    # but we need it to satisfy the type checker
    return "生成报告时出现未知错误。请稍后再试。"


def _build_report_prompt(
    user_id: int, user_data: Dict[str, Any], additional_context: Dict[str, Any]
) -> str:
    """Builds a detailed prompt for the AI to generate a weekly report."""
    # Format achievements for better readability
    achievements_text = ", ".join(user_data.get("new_achievements", [])) or "无"

    # Get time-based greeting
    current_hour = datetime.datetime.now().hour
    time_greeting = (
        "早上好"
        if 5 <= current_hour < 12
        else "下午好" if 12 <= current_hour < 18 else "晚上好"
    )

    # Get day of week in Chinese
    days_in_chinese = [
        "星期一",
        "星期二",
        "星期三",
        "星期四",
        "星期五",
        "星期六",
        "星期日",
    ]
    today_chinese = days_in_chinese[datetime.datetime.now().weekday()]

    # Build the prompt with enhanced personalization
    prompt = f"""
You are a data analyst and motivational coach for the Kindness Companion app.
Your task is to generate a personalized weekly progress report for user {user_data.get('username', '亲爱的用户')}.

User Data for the Past Week:
{{
    "完成打卡次数": {user_data.get('check_ins', 0)},
    "当前连胜天数": {user_data.get('streak', 0)},
    "撰写反思次数": {user_data.get('reflections', 0)},
    "主要参与的挑战类别": {user_data.get('top_category', '无')},
    "解锁成就": {achievements_text}
}}
Trends Compared to the Previous Week:
{{
    "与上周相比": "增加" if additional_context.get('previous_week_check_ins', 0) < user_data.get('check_ins', 0) else "减少",
    "本周完成率": f"{additional_context.get('completion_rate', 0) * 100:.1f}%"
}}
Additional Context:
{{
    "参与的总挑战数": {additional_context.get('total_challenges', 0)}
}}

Instructions for Generating the Report:
1.  **Tone:** Warm, encouraging, supportive, and insightful, like a friendly coach celebrating progress and offering gentle guidance.
2.  **Length:** Concise, around 3-5 sentences.
3.  **Content:**
    *   Start with a friendly, personalized greeting using the user's name.
    *   Acknowledge the user's effort and consistency (or lack thereof, gently).
    *   Highlight 1-2 key achievements or positive trends using specific data (e.g., "Great job completing the '{user_data.get('top_category', '无')}' challenge 5 times!" or "Your streak is growing!").
    *   If specific challenge titles are available in the data, try to mention one.
    *   Briefly mention a trend (e.g., "You focused more on {user_data.get('top_category', '无')} this week.").
    *   If the user unlocked achievements, congratulate them specifically.
    *   If data is sparse or shows a decline, focus on encouragement for the upcoming week ("Every small step counts!", "Let's make next week even better!"). Avoid sounding critical.
    *   End with a positive and forward-looking statement.
4.  **Style:**
    *   Use clear and simple language.
    *   Vary sentence structure and vocabulary to avoid repetition.
    *   Directly address the user (use "你", "你的").
5.  **Output Format:** Respond *only* with the report text itself. Do not include any preamble, explanation, or labels like "Report:".

Generate the report now based *only* on the provided data and instructions.
"""

    return prompt


def _post_process_report(report_text: str) -> str:
    """
    Post-processes the report text to remove unwanted prefixes or format issues.

    Args:
        report_text: The raw report text from the API.

    Returns:
        The cleaned report text.
    """
    # Remove common prefixes that the AI might add
    prefixes_to_remove = [
        "以下是为用户生成的周报：",
        "这是您的周报：",
        "周报：",
        "善行周报：",
        "善行伴侣周报：",
    ]

    cleaned_text = report_text
    for prefix in prefixes_to_remove:
        if cleaned_text.startswith(prefix):
            cleaned_text = cleaned_text[len(prefix) :].strip()

    return cleaned_text


def _get_additional_context(
    user_id: int, current_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Gets additional context for the report to make it more personalized.

    Args:
        user_id: The ID of the user.
        current_data: The current week's data.

    Returns:
        A dictionary containing additional context.
    """
    try:
        # Import backend modules here to avoid circular imports
        from backend.database_manager import DatabaseManager
        from backend.progress_tracker import ProgressTracker
        from backend.challenge_manager import ChallengeManager

        # Initialize backend components
        db_manager = DatabaseManager()
        progress_tracker = ProgressTracker(db_manager)
        challenge_manager = ChallengeManager(db_manager)

        # Get data for the previous week for comparison
        end_date = datetime.date.today() - datetime.timedelta(days=7)
        start_date = end_date - datetime.timedelta(days=7)

        # Get check-ins for the previous week
        previous_check_ins = progress_tracker.get_all_user_check_ins(
            user_id, start_date.isoformat(), end_date.isoformat()
        )

        # Get total number of challenges the user is participating in
        subscribed_challenges = challenge_manager.get_user_challenges(user_id)

        # Calculate completion rate for the current week
        # (Number of unique days with check-ins / 7 days)
        unique_days = set()

        # Get check-ins for the current week again to count unique days
        current_week_data = progress_tracker.get_all_user_check_ins(
            user_id,
            (datetime.date.today() - datetime.timedelta(days=7)).isoformat(),
            datetime.date.today().isoformat(),
        )

        for check_in in current_week_data:
            if "check_in_date" in check_in:
                unique_days.add(check_in["check_in_date"])

        completion_rate = len(unique_days) / 7 if unique_days else 0

        return {
            "previous_week_check_ins": len(previous_check_ins),
            "total_challenges": len(subscribed_challenges),
            "completion_rate": completion_rate,
        }
    except Exception as e:
        logger.warning(f"Error getting additional context: {e}")
        return {}


def _get_user_data_for_report(user_id: int) -> Dict[str, Any]:
    """
    Fetches aggregated user data needed for the report for the past week.
    """
    logger.info(f"Fetching report data for user {user_id}")

    try:
        # Import backend modules here to avoid circular imports
        from backend.database_manager import DatabaseManager
        from backend.progress_tracker import ProgressTracker
        from backend.challenge_manager import ChallengeManager

        # Initialize backend components
        db_manager = DatabaseManager()
        progress_tracker = ProgressTracker(db_manager)
        challenge_manager = ChallengeManager(db_manager)

        # Get data for the past week
        import datetime

        end_date = datetime.date.today()
        start_date = end_date - datetime.timedelta(days=7)

        # Get check-ins for the past week
        check_ins = progress_tracker.get_all_user_check_ins(
            user_id, start_date.isoformat(), end_date.isoformat()
        )

        # Count total check-ins
        total_check_ins = len(check_ins)

        # Count reflections (check-ins with non-empty notes)
        reflections = sum(
            1 for ci in check_ins if ci.get("notes") and ci.get("notes").strip()
        )

        # Get current streak across all challenges
        longest_streak = progress_tracker.get_longest_streak_all_challenges(user_id)

        # Get top category
        category_counts = {}
        for ci in check_ins:
            challenge = challenge_manager.get_challenge_by_id(ci.get("challenge_id"))
            if challenge and "category" in challenge:
                category = challenge["category"]
                category_counts[category] = category_counts.get(category, 0) + 1

        top_category = (
            "无"
            if not category_counts
            else max(category_counts, key=lambda x: category_counts[x])
        )

        # Get newly achieved milestones
        # For simplicity, we'll just check if any achievements were reached in the past week
        # A more sophisticated implementation would track when achievements were unlocked
        all_check_ins = progress_tracker.get_total_check_ins(user_id)
        new_achievements = []

        # Check for check-in milestones
        for milestone, name in [
            (10, "善行初学者"),
            (50, "善行践行者"),
            (100, "善意大师"),
        ]:
            if (
                all_check_ins >= milestone
                and all_check_ins - total_check_ins < milestone
            ):
                new_achievements.append(name)

        # Check for streak milestones
        for milestone, name in [(7, "坚持不懈"), (14, "毅力之星"), (30, "恒心典范")]:
            if longest_streak >= milestone:
                new_achievements.append(name)

        # Return the aggregated data
        return {
            "check_ins": total_check_ins,
            "streak": longest_streak,
            "reflections": reflections,
            "top_category": top_category,
            "new_achievements": new_achievements,
        }
    except Exception as e:
        logger.error(f"Error fetching user data for report: {e}", exc_info=True)
        # Return fallback data if there's an error
        return {
            "check_ins": 0,
            "streak": 0,
            "reflections": 0,
            "top_category": "无",
            "new_achievements": [],
        }


def _call_text_generation_api(prompt: str) -> str | None:
    """
    Private helper function to call the configured text generation API (ZhipuAI Chat).
    Requires API key management.
    """
    api_key = get_api_key("ZHIPUAI")
    if not api_key:
        logger.error("ZhipuAI API key not found. Cannot call text generation API.")
        return None

    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    payload = {
        "model": DEFAULT_MODEL,
        "messages": [
            {
                "role": "system",
                "content": "You are an assistant for the Kindness Companion app. Generate encouraging weekly summaries based on user data. Keep the tone positive and warm. Respond in Chinese.",
            },  # Added Chinese response instruction
            {"role": "user", "content": prompt},
        ],
        "max_tokens": 150,  # Allow slightly longer responses for reports
        "temperature": 0.7,
    }

    try:
        logger.debug(f"Calling ZhipuAI Text Generation API. Model: {DEFAULT_MODEL}")
        response_data = make_api_request(
            method="POST", url=ZHIPUAI_API_ENDPOINT, headers=headers, data=payload
        )

        # Extract the response text
        if response_data and "choices" in response_data and response_data["choices"]:
            message = response_data["choices"][0].get("message")
            if message and "content" in message:
                report = message["content"].strip()
                logger.info(f"Received report text from API: {report[:50]}...")
                return report
            else:
                logger.warning(
                    f"Unexpected response structure from ZhipuAI API (Report): No message content. Response: {response_data}"
                )
                return None
        else:
            logger.warning(
                f"Unexpected response structure or empty choices from ZhipuAI API (Report): {response_data}"
            )
            return None

    except RequestException as e:
        logger.error(f"ZhipuAI API request failed (Report): {e}")
        return None
    except Exception as e:
        logger.error(f"An unexpected error occurred calling ZhipuAI API (Report): {e}")
        return None
