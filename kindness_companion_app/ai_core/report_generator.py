import logging
from typing import Dict, Any
from .api_client import get_api_key, make_api_request
from requests.exceptions import RequestException

logger = logging.getLogger(__name__)
ZHIPUAI_API_ENDPOINT = "https://open.bigmodel.cn/api/paas/v4/chat/completions" # Reusing chat endpoint
DEFAULT_MODEL = "glm-4-flash" # Or a model suitable for summarization/reporting

def generate_weekly_report(user_id: int) -> str:
    """
    Generates a personalized weekly kindness report for the user using an AI API.
    """
    logger.info(f"Generating weekly report for user {user_id}.")

    # 1. Fetch user data for the report period (Placeholder)
    try:
        user_data = _get_user_data_for_report(user_id)
        if not user_data:
            logger.warning("No user data found to generate report.")
            return "无法生成报告，似乎还没有足够的活动数据。"
    except Exception as e:
        logger.error(f"Error fetching user data for report: {e}")
        return "生成报告时出错（获取数据失败）。"

    # 2. Construct a prompt for the text generation API
    prompt = f"""
为 Kindness Companion 应用的用户生成一份简短（2-3句话）且鼓励性的周报总结。
用户 ID: {user_id}
本周数据:
- 完成打卡次数: {user_data.get('check_ins', 0)}
- 当前连胜天数: {user_data.get('streak', 0)}
- 撰写反思次数: {user_data.get('reflections', 0)}
- 主要参与的挑战类别: {user_data.get('top_category', '无')}
- 解锁成就: {', '.join(user_data.get('new_achievements', [])) or '无'}

请根据以上数据，生成一段积极、温暖、鼓励用户继续行善的文字。可以提及具体数据，例如连胜或打卡次数。
"""

    # 3. Call the text generation API
    try:
        report_text = _call_text_generation_api(prompt)
        if not report_text:
            logger.warning("Text generation API returned empty response for report.")
            return "AI 正在思考中，暂时无法生成报告..."
        logger.info(f"Generated report text (first 50 chars): {report_text[:50]}...")
        # Return only the generated text, formatting can happen in the UI
        return report_text
    except Exception as e:
        logger.error(f"Error calling text generation API for report: {e}")
        return "生成报告时与 AI 连接出现问题。"


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
            user_id,
            start_date.isoformat(),
            end_date.isoformat()
        )

        # Count total check-ins
        total_check_ins = len(check_ins)

        # Count reflections (check-ins with non-empty notes)
        reflections = sum(1 for ci in check_ins if ci.get("notes") and ci.get("notes").strip())

        # Get current streak across all challenges
        longest_streak = progress_tracker.get_longest_streak_all_challenges(user_id)

        # Get top category
        category_counts = {}
        for ci in check_ins:
            challenge = challenge_manager.get_challenge_by_id(ci.get("challenge_id"))
            if challenge and "category" in challenge:
                category = challenge["category"]
                category_counts[category] = category_counts.get(category, 0) + 1

        top_category = "无" if not category_counts else max(category_counts, key=category_counts.get)

        # Get newly achieved milestones
        # For simplicity, we'll just check if any achievements were reached in the past week
        # A more sophisticated implementation would track when achievements were unlocked
        all_check_ins = progress_tracker.get_total_check_ins(user_id)
        new_achievements = []

        # Check for check-in milestones
        for milestone, name in [(10, "善行初学者"), (50, "善行践行者"), (100, "善意大师")]:
            if all_check_ins >= milestone and all_check_ins - total_check_ins < milestone:
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
            "new_achievements": new_achievements
        }
    except Exception as e:
        logger.error(f"Error fetching user data for report: {e}", exc_info=True)
        # Return fallback data if there's an error
        return {
            "check_ins": 0,
            "streak": 0,
            "reflections": 0,
            "top_category": "无",
            "new_achievements": []
        }

def _call_text_generation_api(prompt: str) -> str | None:
    """
    Private helper function to call the configured text generation API (ZhipuAI Chat).
    Requires API key management.
    """
    api_key = get_api_key('ZHIPUAI')
    if not api_key:
        logger.error("ZhipuAI API key not found. Cannot call text generation API.")
        return None

    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }

    payload = {
        "model": DEFAULT_MODEL,
        "messages": [
            {"role": "system", "content": "You are an assistant for the Kindness Companion app. Generate encouraging weekly summaries based on user data. Keep the tone positive and warm. Respond in Chinese."}, # Added Chinese response instruction
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 150, # Allow slightly longer responses for reports
        "temperature": 0.7
    }

    try:
        logger.debug(f"Calling ZhipuAI Text Generation API. Model: {DEFAULT_MODEL}")
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
                report = message['content'].strip()
                logger.info(f"Received report text from API: {report[:50]}...")
                return report
            else:
                logger.warning(f"Unexpected response structure from ZhipuAI API (Report): No message content. Response: {response_data}")
                return None
        else:
            logger.warning(f"Unexpected response structure or empty choices from ZhipuAI API (Report): {response_data}")
            return None

    except RequestException as e:
        logger.error(f"ZhipuAI API request failed (Report): {e}")
        return None
    except Exception as e:
        logger.error(f"An unexpected error occurred calling ZhipuAI API (Report): {e}")
        return None
