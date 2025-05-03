"""
Test script to verify ZhipuAI API key and connection.
"""

import logging
import sys
from zhipuai import ZhipuAI

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import API key from config
try:
    from config import ZHIPUAI_API_KEY
    logger.info("Successfully imported API key from config.py")
except ImportError:
    logger.error("Failed to import ZHIPUAI_API_KEY from config.py")
    sys.exit(1)

def test_zhipuai_connection():
    """Test connection to ZhipuAI API."""
    logger.info(f"Testing ZhipuAI API connection with key: {ZHIPUAI_API_KEY[:5]}...{ZHIPUAI_API_KEY[-5:]}")
    
    try:
        # Initialize client
        client = ZhipuAI(api_key=ZHIPUAI_API_KEY)
        logger.info("Successfully initialized ZhipuAI client")
        
        # Test a simple completion
        messages = [
            {"role": "user", "content": "你好，请用一句话回复我"}
        ]
        
        logger.info("Sending test request to ZhipuAI API...")
        response = client.chat.completions.create(
            model="glm-4-flash-250414",
            messages=messages,
        )
        
        logger.info(f"Received response from ZhipuAI API: {response}")
        
        if response and response.choices:
            content = response.choices[0].message.content
            logger.info(f"API response content: {content}")
            return True
        else:
            logger.error("Response structure unexpected or empty")
            return False
            
    except Exception as e:
        logger.error(f"Error testing ZhipuAI API: {e}")
        return False

if __name__ == "__main__":
    logger.info("Starting ZhipuAI API test")
    success = test_zhipuai_connection()
    
    if success:
        logger.info("✅ ZhipuAI API test successful!")
        sys.exit(0)
    else:
        logger.error("❌ ZhipuAI API test failed!")
        sys.exit(1)
