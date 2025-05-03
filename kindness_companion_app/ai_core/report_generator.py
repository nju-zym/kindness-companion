from typing import List, Dict

# TODO: Implement AI report generation (as described in README)
# This involves:
# 1. Aggregating relevant user data (e.g., check-ins, streaks, reflections) from the database (via backend modules).
# 2. Constructing a suitable prompt for the text generation API.
# 3. Calling the text generation API (e.g., GPT).
# 4. Formatting the response into a user-friendly report.
# 5. Potentially generating visualizations locally (e.g., using Matplotlib) or via API if supported.

def generate_weekly_report(user_id: int) -> str:
    """
    Generates a personalized weekly summary report for the user using an AI text generation API.

    Args:
        user_id: The ID of the user for whom to generate the report.

    Returns:
        A string containing the formatted weekly report.
    """
    # 1. Fetch data for the last week (replace with actual backend calls)
    user_data = _get_user_data_for_report(user_id)

    # 2. Create prompt
    prompt = f"Generate a kind and encouraging weekly summary for user {user_id} based on this data: {user_data}. Highlight progress and streaks."

    # 3. Call API
    report_text = _call_text_generation_api(prompt)

    # 4. Format (basic example)
    formatted_report = f"## Your Weekly Kindness Summary\n\n{report_text}\n\nKeep up the amazing work!"

    # 5. Optional: Add visualization (placeholder)
    # report_visualization = _generate_report_visualization(user_data)
    # formatted_report += f"\n\n![Progress Chart]({report_visualization})" # Example if saving image

    print(f"Generated report for user {user_id}") # Placeholder
    return formatted_report

def _get_user_data_for_report(user_id: int) -> Dict:
    """Placeholder: Fetches aggregated user data needed for the report."""
    # This function would interact with backend.database_manager, backend.progress_tracker etc.
    print(f"Fetching report data for user {user_id}") # Placeholder
    return {"check_ins": 5, "streak": 3, "reflections": 2} # Example data

def _call_text_generation_api(prompt: str) -> str:
    """
    Private helper function to call the configured text generation API.
    Requires API key management.
    """
    # Implementation depends on the chosen API (e.g., OpenAI, Gemini)
    # Use api_client.py if available
    print(f"Calling Text Generation API with prompt: {prompt}") # Placeholder
    return "You've done a great job this week, especially with keeping your streak going!" # Placeholder response

# def _generate_report_visualization(data: Dict) -> str:
#     """Placeholder: Generates a visualization (e.g., chart) and returns its path or data URI."""
#     # Use matplotlib or similar library
#     print("Generating report visualization...")
#     return "path/to/chart.png" # Placeholder
