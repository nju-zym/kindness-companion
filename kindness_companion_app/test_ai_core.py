"""
Test script to verify AI core functionality.
"""

import logging
import sys
import os

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the parent directory to sys.path to ensure imports work correctly
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)
    logger.info(f"Added {parent_dir} to sys.path")

# Print current working directory and sys.path for debugging
logger.info(f"Current working directory: {os.getcwd()}")
logger.info(f"sys.path: {sys.path}")

# Try importing the AI core modules
try:
    from kindness_companion_app.ai_core.pet_handler import handle_pet_event
    logger.info("Successfully imported handle_pet_event")
except ImportError as e:
    logger.error(f"Failed to import handle_pet_event: {e}")
    
    # Try alternative import path
    try:
        from ai_core.pet_handler import handle_pet_event
        logger.info("Successfully imported handle_pet_event using alternative path")
    except ImportError as e:
        logger.error(f"Failed to import handle_pet_event using alternative path: {e}")
        
        # Try to import the modules directly to see where the issue is
        try:
            import kindness_companion_app.ai_core
            logger.info("Successfully imported kindness_companion_app.ai_core")
        except ImportError as e:
            logger.error(f"Failed to import kindness_companion_app.ai_core: {e}")
            
        try:
            import ai_core
            logger.info("Successfully imported ai_core")
        except ImportError as e:
            logger.error(f"Failed to import ai_core: {e}")

# Test the AI core functionality if imports succeeded
if 'handle_pet_event' in locals():
    logger.info("Testing handle_pet_event function")
    
    try:
        # Test with a simple user message event
        user_id = 1
        event_type = 'user_message'
        event_data = {'message': '你好，宠物！'}
        
        logger.info(f"Calling handle_pet_event with: user_id={user_id}, event_type={event_type}, event_data={event_data}")
        response = handle_pet_event(user_id, event_type, event_data)
        
        logger.info(f"Received response from handle_pet_event: {response}")
        
        if response and 'dialogue' in response:
            logger.info(f"AI response dialogue: {response['dialogue']}")
            logger.info("✅ AI core test successful!")
        else:
            logger.error("Response structure unexpected or empty")
            logger.error("❌ AI core test failed!")
    except Exception as e:
        logger.error(f"Error testing handle_pet_event: {e}", exc_info=True)
        logger.error("❌ AI core test failed!")
else:
    logger.error("Cannot test handle_pet_event because import failed")
    logger.error("❌ AI core test failed!")

if __name__ == "__main__":
    logger.info("AI core test completed")
