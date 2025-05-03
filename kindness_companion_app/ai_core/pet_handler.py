# ai_pet_handler.py

import logging
from typing import Dict, Any

# Need to import functions from other ai_core modules
from .dialogue_generator import generate_pet_dialogue
from .emotion_analyzer import analyze_emotion_for_pet

logger = logging.getLogger(__name__)

def handle_pet_event(user_id: int, event_type: str, event_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handles events triggered by user actions and determines the pet's response.

    Args:
        user_id: The ID of the user.
        event_type: The type of event (e.g., 'check_in', 'reflection_added').
        event_data: Data associated with the event (e.g., reflection text, challenge details).

    Returns:
        A dictionary containing the pet's response, e.g.:
        {'dialogue': 'Woof! Great job!', 'emotion_detected': 'positive', 'suggested_animation': 'happy'}
    """
    logger.info(f"Handling pet event for user {user_id}. Type: {event_type}")

    emotion = None
    dialogue_prompt_context = event_data.copy() # Start with base event data

    # 1. Analyze emotion if it's a reflection event or user message
    if event_type == 'reflection_added' and 'text' in event_data:
        reflection_text = event_data.get('text', '')
        if reflection_text:
            try:
                emotion = analyze_emotion_for_pet(user_id, reflection_text)
                if emotion:
                    dialogue_prompt_context['analyzed_emotion'] = emotion # Add emotion to context for dialogue generation
                    logger.info(f"Analyzed emotion for reflection: {emotion}")
                else:
                    logger.warning("Emotion analysis returned None.")
            except Exception as e:
                logger.error(f"Error during emotion analysis: {e}")
        else:
            logger.warning("Reflection event received but no text found in event_data.")

    # Handle direct user messages
    elif event_type == 'user_message' and 'message' in event_data:
        user_message = event_data.get('message', '')
        if user_message:
            try:
                # Optionally analyze emotion for user messages too
                emotion = analyze_emotion_for_pet(user_id, user_message)
                if emotion:
                    dialogue_prompt_context['analyzed_emotion'] = emotion
                    logger.info(f"Analyzed emotion for user message: {emotion}")
            except Exception as e:
                logger.error(f"Error during emotion analysis for user message: {e}")
        else:
            logger.warning("User message event received but no message found in event_data.")

    # 2. Generate dialogue based on the event and context (including potential emotion)
    try:
        dialogue = generate_pet_dialogue(user_id, event_type, dialogue_prompt_context)
    except Exception as e:
        logger.error(f"Error during dialogue generation: {e}")
        dialogue = "... (The pet seems lost in thought)"

    # 3. Determine suggested animation/state (Simple logic for now)
    suggested_animation = 'idle' # Default animation
    if event_type == 'check_in':
        suggested_animation = 'happy' # Simple positive feedback for check-in
    elif event_type == 'user_message':
        # For user messages, base animation on detected emotion or default to 'happy'
        if emotion == 'positive':
            suggested_animation = 'excited'
        elif emotion == 'negative':
            suggested_animation = 'concerned'
        else:
            suggested_animation = 'happy'  # Default for user messages
    elif emotion == 'positive':
        suggested_animation = 'excited'
    elif emotion == 'negative':
        suggested_animation = 'concerned' # Or 'supportive'

    logger.info(f"Pet response generated. Dialogue: '{dialogue[:30]}...', Animation: {suggested_animation}")

    # 4. Return the combined response
    return {
        'dialogue': dialogue,
        'emotion_detected': emotion, # Include detected emotion if any
        'suggested_animation': suggested_animation
    }

# Example Usage (for testing purposes):
# if __name__ == '__main__':
#     logging.basicConfig(level=logging.INFO)
#     # Mock event data
#     check_in_event = {'challenge_id': 1, 'challenge_title': 'Daily Smile'}
#     reflection_event_pos = {'text': 'Feeling great after helping someone today!'}
#     reflection_event_neg = {'text': 'Felt a bit down, but I tried my best.'}
#     reflection_event_neutral = {'text': 'Just finished the task.'}
#
#     print("--- Check-in Event ---")
#     response_checkin = handle_pet_event(1, 'check_in', check_in_event)
#     print(response_checkin)
#
#     print("\n--- Positive Reflection Event ---")
#     response_pos = handle_pet_event(1, 'reflection_added', reflection_event_pos)
#     print(response_pos)
#
#     print("\n--- Negative Reflection Event ---")
#     response_neg = handle_pet_event(1, 'reflection_added', reflection_event_neg)
#     print(response_neg)
#
#     print("\n--- Neutral Reflection Event ---")
#     response_neutral = handle_pet_event(1, 'reflection_added', reflection_event_neutral)
#     print(response_neutral)