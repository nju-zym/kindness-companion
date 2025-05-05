# ai_pet_handler.py

import logging
from typing import Dict, Any, Optional

# Import functions from other ai_core modules
from .dialogue_generator import generate_pet_dialogue
from .emotion_analyzer import analyze_emotion_for_pet
from .enhanced_dialogue_generator import EnhancedDialogueGenerator

logger = logging.getLogger(__name__)

# Global instance of EnhancedDialogueGenerator
# Will be initialized when db_manager is available
_enhanced_dialogue_generator: Optional[EnhancedDialogueGenerator] = None

def initialize_enhanced_dialogue(db_manager):
    """
    Initialize the enhanced dialogue generator with a database manager.

    Args:
        db_manager: Database manager instance
    """
    global _enhanced_dialogue_generator
    if _enhanced_dialogue_generator is None:
        logger.info("Initializing enhanced dialogue generator")
        _enhanced_dialogue_generator = EnhancedDialogueGenerator(db_manager)
    return _enhanced_dialogue_generator

def handle_pet_event(user_id: int, event_type: str, event_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handles events triggered by user actions and determines the pet's response.
    Now supports enhanced dialogue with psychological analysis and extended context.

    Args:
        user_id: The ID of the user.
        event_type: The type of event (e.g., 'check_in', 'reflection_added').
        event_data: Data associated with the event (e.g., reflection text, challenge details).

    Returns:
        A dictionary containing the pet's response, e.g.:
        {'dialogue': 'Woof! Great job!', 'emotion_detected': 'positive', 'suggested_animation': 'happy'}
    """
    logger.info(f"Handling pet event for user {user_id}. Type: {event_type}")

    # Check if enhanced dialogue generator is available
    global _enhanced_dialogue_generator
    use_enhanced = _enhanced_dialogue_generator is not None

    emotion = None
    dialogue_prompt_context = event_data.copy() # Start with base event data

    # 1. Analyze emotion if it's a reflection event or user message
    emotion = None
    suggested_animation = 'idle'  # Default animation

    if event_type == 'reflection_added' and 'text' in event_data:
        reflection_text = event_data.get('text', '')
        if reflection_text:
            try:
                emotion, suggested_animation = analyze_emotion_for_pet(user_id, reflection_text)
                if emotion:
                    dialogue_prompt_context['analyzed_emotion'] = emotion  # Add emotion to context for dialogue generation
                    dialogue_prompt_context['suggested_animation'] = suggested_animation  # Add suggested animation
                    logger.info(f"Analyzed emotion for reflection: {emotion}, suggested animation: {suggested_animation}")
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
                # Analyze emotion for user messages
                emotion, suggested_animation = analyze_emotion_for_pet(user_id, user_message)
                if emotion:
                    dialogue_prompt_context['analyzed_emotion'] = emotion
                    dialogue_prompt_context['suggested_animation'] = suggested_animation
                    logger.info(f"Analyzed emotion for user message: {emotion}, suggested animation: {suggested_animation}")
            except Exception as e:
                logger.error(f"Error during emotion analysis for user message: {e}")
        else:
            logger.warning("User message event received but no message found in event_data.")

    # 2. Generate dialogue based on the event and context
    try:
        if use_enhanced:
            # Use enhanced dialogue generator with psychological analysis and extended context
            logger.info("Using enhanced dialogue generator")
            response = _enhanced_dialogue_generator.generate_dialogue(user_id, event_type, dialogue_prompt_context)
            dialogue = response['dialogue']
            suggested_animation = response['suggested_animation']

            logger.info(f"Enhanced dialogue generated. Context ID: {response.get('context_id')}")

            # Return enhanced response
            return {
                'dialogue': dialogue,
                'emotion_detected': emotion,  # Include detected emotion if any
                'suggested_animation': suggested_animation,
                'context_id': response.get('context_id'),
                'profile_available': response.get('profile_available', False)
            }
        else:
            # Fall back to original dialogue generator
            logger.info("Using original dialogue generator (enhanced generator not initialized)")
            dialogue = generate_pet_dialogue(user_id, event_type, dialogue_prompt_context)

            # Use the suggested animation from emotion analysis if available
            if 'suggested_animation' in dialogue_prompt_context:
                suggested_animation = dialogue_prompt_context['suggested_animation']
            # Otherwise, determine animation based on event type and basic emotion
            else:
                suggested_animation = 'idle'  # Default animation
                if event_type == 'check_in':
                    suggested_animation = 'happy'  # Simple positive feedback for check-in
                elif event_type == 'user_message' or event_type == 'reflection_added':
                    # For user messages and reflections, base animation on detected emotion
                    if emotion in ['positive', 'happy', 'excited', 'joyful', 'content', 'proud', 'grateful', 'optimistic']:
                        suggested_animation = 'excited' if emotion in ['excited', 'joyful', 'proud'] else 'happy'
                    elif emotion in ['negative', 'sad', 'anxious', 'worried', 'frustrated', 'angry', 'disappointed', 'stressed']:
                        suggested_animation = 'concerned'
                    elif emotion in ['surprised', 'confused', 'uncertain']:
                        suggested_animation = 'confused'
                    else:
                        suggested_animation = 'happy'  # Default for user messages

            logger.info(f"Pet response generated. Dialogue: '{dialogue[:30]}...', Animation: {suggested_animation}")

            # Return the combined response
            return {
                'dialogue': dialogue,
                'emotion_detected': emotion, # Include detected emotion if any
                'suggested_animation': suggested_animation
            }
    except Exception as e:
        logger.error(f"Error during dialogue generation: {e}")
        dialogue = "... (The pet seems lost in thought)"

        # Return fallback response
        return {
            'dialogue': dialogue,
            'emotion_detected': emotion,
            'suggested_animation': 'confused'
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