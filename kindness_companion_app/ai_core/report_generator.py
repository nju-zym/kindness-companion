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
    Placeholder: Fetches aggregated user data needed for the report for the past week.
    TODO: Replace with actual database queries using backend modules.
    """
    logger.info(f"Fetching report data for user {user_id} (using placeholder data).")
    # Return mock data for now
    return {
        "check_ins": 5,
        "streak": 3,
        "reflections": 2,
        "top_category": "社区服务",
        "new_achievements": ["善意新手"]
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
