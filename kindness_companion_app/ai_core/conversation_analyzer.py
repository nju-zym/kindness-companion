"""
Conversation analyzer module for analyzing user psychological characteristics.

This module provides functionality to:
1. Analyze user messages for psychological traits
2. Store and retrieve user psychological profiles
3. Adjust dialogue style based on user profiles
4. Manage conversation history for extended context
"""

import logging
import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

from .api_client import get_api_key, make_api_request

logger = logging.getLogger(__name__)

# API configuration
ZHIPUAI_API_ENDPOINT = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
DEFAULT_MODEL = "glm-4" # Using GLM-4 for more advanced analysis capabilities

class ConversationAnalyzer:
    """
    Analyzes conversations to determine user psychological characteristics
    and adjusts dialogue style accordingly.
    """
    
    def __init__(self, db_manager):
        """
        Initialize the conversation analyzer.
        
        Args:
            db_manager: Database manager instance for storing and retrieving data
        """
        self.db_manager = db_manager
        self._ensure_tables_exist()
        
    def _ensure_tables_exist(self):
        """Ensure that the necessary database tables exist."""
        # Create conversation_history table
        self.db_manager.connect()
        
        # Create conversation_history table
        self.db_manager.cursor.execute('''
        CREATE TABLE IF NOT EXISTS conversation_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            message TEXT NOT NULL,
            is_user BOOLEAN NOT NULL,  -- True if message is from user, False if from AI
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            context_id TEXT,  -- Group conversations by context
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        ''')
        
        # Create user_psychological_profile table
        self.db_manager.cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_psychological_profile (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL,
            profile_data TEXT NOT NULL,  -- JSON string containing psychological profile
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            confidence_score FLOAT,  -- Confidence in the profile analysis (0.0-1.0)
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        ''')
        
        # Create dialogue_style_preferences table
        self.db_manager.cursor.execute('''
        CREATE TABLE IF NOT EXISTS dialogue_style_preferences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL,
            formality_level INTEGER,  -- 1-5 scale (1: very casual, 5: very formal)
            verbosity_level INTEGER,  -- 1-5 scale (1: very concise, 5: very verbose)
            empathy_level INTEGER,    -- 1-5 scale (1: very factual, 5: very empathetic)
            humor_level INTEGER,      -- 1-5 scale (1: very serious, 5: very humorous)
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        ''')
        
        self.db_manager.connection.commit()
        self.db_manager.disconnect()
    
    def store_message(self, user_id: int, message: str, is_user: bool, context_id: Optional[str] = None) -> int:
        """
        Store a message in the conversation history.
        
        Args:
            user_id: User ID
            message: Message content
            is_user: True if message is from user, False if from AI
            context_id: Optional context ID to group related messages
            
        Returns:
            ID of the stored message
        """
        if not context_id:
            # Generate a context ID based on timestamp if not provided
            context_id = f"ctx_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
        message_id = self.db_manager.execute_insert(
            """
            INSERT INTO conversation_history (user_id, message, is_user, context_id)
            VALUES (?, ?, ?, ?)
            """,
            (user_id, message, 1 if is_user else 0, context_id)
        )
        
        logger.debug(f"Stored message (ID: {message_id}) for user {user_id} in context {context_id}")
        return message_id
    
    def get_conversation_history(self, user_id: int, limit: int = 20, context_id: Optional[str] = None) -> List[Dict]:
        """
        Retrieve conversation history for a user.
        
        Args:
            user_id: User ID
            limit: Maximum number of messages to retrieve
            context_id: Optional context ID to filter by specific conversation
            
        Returns:
            List of message dictionaries
        """
        query = """
        SELECT * FROM conversation_history
        WHERE user_id = ?
        """
        params = [user_id]
        
        if context_id:
            query += " AND context_id = ?"
            params.append(context_id)
            
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        messages = self.db_manager.execute_query(query, tuple(params))
        
        # Convert to more usable format and reverse to get chronological order
        formatted_messages = []
        for msg in reversed(messages):
            formatted_messages.append({
                'id': msg['id'],
                'content': msg['message'],
                'role': 'user' if msg['is_user'] else 'assistant',
                'timestamp': msg['timestamp'],
                'context_id': msg['context_id']
            })
            
        return formatted_messages
    
    def analyze_user_psychology(self, user_id: int) -> Dict[str, Any]:
        """
        Analyze user psychological characteristics based on conversation history.
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary containing psychological profile data
        """
        # Get user's conversation history
        messages = self.get_conversation_history(user_id, limit=50)
        
        if not messages:
            logger.warning(f"No conversation history found for user {user_id}")
            return {
                'personality_traits': {},
                'communication_preferences': {},
                'confidence_score': 0.0,
                'last_updated': datetime.now().isoformat()
            }
        
        # Extract only user messages for analysis
        user_messages = [msg['content'] for msg in messages if msg['role'] == 'user']
        
        if not user_messages:
            logger.warning(f"No user messages found in conversation history for user {user_id}")
            return {
                'personality_traits': {},
                'communication_preferences': {},
                'confidence_score': 0.0,
                'last_updated': datetime.now().isoformat()
            }
        
        # Call AI API to analyze user psychology
        profile_data = self._call_psychology_analysis_api(user_messages)
        
        # Store the profile data
        self._store_psychological_profile(user_id, profile_data)
        
        return profile_data
    
    def _call_psychology_analysis_api(self, user_messages: List[str]) -> Dict[str, Any]:
        """
        Call the AI API to analyze user psychological characteristics.
        
        Args:
            user_messages: List of user messages
            
        Returns:
            Dictionary containing psychological profile data
        """
        api_key = get_api_key('ZHIPUAI')
        if not api_key:
            logger.error("ZhipuAI API key not found. Cannot analyze user psychology.")
            return {
                'personality_traits': {},
                'communication_preferences': {},
                'confidence_score': 0.0,
                'last_updated': datetime.now().isoformat()
            }
        
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        # Construct the prompt for psychological analysis
        prompt = f"""
        作为一个心理分析专家，请分析以下用户消息，并提供关于用户心理特征的见解。
        请关注以下方面：
        1. 性格特征（如：外向/内向、乐观/悲观、理性/感性等）
        2. 沟通偏好（如：喜欢详细解释还是简洁回答、正式还是随意的语气、是否喜欢幽默等）
        3. 情感状态（如：当前的情绪倾向、压力水平等）
        4. 思维模式（如：分析型、创造型、实用型等）
        
        用户消息：
        {json.dumps(user_messages, ensure_ascii=False, indent=2)}
        
        请以JSON格式返回分析结果，包含以下字段：
        - personality_traits: 包含性格特征的对象
        - communication_preferences: 包含沟通偏好的对象
        - emotional_state: 包含情感状态的对象
        - thinking_patterns: 包含思维模式的对象
        - confidence_score: 分析的置信度（0.0-1.0）
        
        注意：仅返回JSON格式的结果，不要包含其他文本。如果数据不足以进行可靠分析，请在相应字段中说明。
        """
        
        payload = {
            "model": DEFAULT_MODEL,
            "messages": [
                {"role": "system", "content": "你是一个专业的心理分析专家，擅长从文本中分析用户的心理特征。请只返回JSON格式的分析结果。"},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.2,  # Low temperature for more deterministic results
            "response_format": {"type": "json_object"}  # Request JSON format
        }
        
        try:
            response_data = make_api_request(ZHIPUAI_API_ENDPOINT, headers=headers, json_payload=payload)
            
            if response_data and 'choices' in response_data and response_data['choices']:
                # Extract the JSON response
                content = response_data['choices'][0].get('message', {}).get('content', '{}')
                try:
                    profile_data = json.loads(content)
                    # Add timestamp
                    profile_data['last_updated'] = datetime.now().isoformat()
                    return profile_data
                except json.JSONDecodeError:
                    logger.error(f"Failed to parse JSON response: {content}")
            
            logger.warning("Invalid or empty response from psychology analysis API")
            
        except Exception as e:
            logger.error(f"Error calling psychology analysis API: {e}")
        
        # Return empty profile if API call fails
        return {
            'personality_traits': {},
            'communication_preferences': {},
            'emotional_state': {},
            'thinking_patterns': {},
            'confidence_score': 0.0,
            'last_updated': datetime.now().isoformat()
        }
    
    def _store_psychological_profile(self, user_id: int, profile_data: Dict[str, Any]) -> bool:
        """
        Store or update the psychological profile for a user.
        
        Args:
            user_id: User ID
            profile_data: Psychological profile data
            
        Returns:
            True if successful, False otherwise
        """
        # Check if profile already exists
        existing_profile = self.db_manager.execute_query(
            "SELECT id FROM user_psychological_profile WHERE user_id = ?",
            (user_id,)
        )
        
        profile_json = json.dumps(profile_data, ensure_ascii=False)
        confidence_score = profile_data.get('confidence_score', 0.0)
        
        if existing_profile:
            # Update existing profile
            success = self.db_manager.execute_update(
                """
                UPDATE user_psychological_profile
                SET profile_data = ?, last_updated = CURRENT_TIMESTAMP, confidence_score = ?
                WHERE user_id = ?
                """,
                (profile_json, confidence_score, user_id)
            ) > 0
        else:
            # Insert new profile
            success = self.db_manager.execute_insert(
                """
                INSERT INTO user_psychological_profile (user_id, profile_data, confidence_score)
                VALUES (?, ?, ?)
                """,
                (user_id, profile_json, confidence_score)
            ) > 0
        
        if success:
            logger.info(f"Stored psychological profile for user {user_id}")
            # Update dialogue style preferences based on profile
            self._update_dialogue_style_preferences(user_id, profile_data)
        else:
            logger.error(f"Failed to store psychological profile for user {user_id}")
            
        return success
    
    def _update_dialogue_style_preferences(self, user_id: int, profile_data: Dict[str, Any]) -> bool:
        """
        Update dialogue style preferences based on psychological profile.
        
        Args:
            user_id: User ID
            profile_data: Psychological profile data
            
        Returns:
            True if successful, False otherwise
        """
        # Extract communication preferences from profile
        comm_prefs = profile_data.get('communication_preferences', {})
        personality = profile_data.get('personality_traits', {})
        
        # Map preferences to dialogue style parameters (1-5 scale)
        formality_level = self._map_formality_level(comm_prefs, personality)
        verbosity_level = self._map_verbosity_level(comm_prefs, personality)
        empathy_level = self._map_empathy_level(comm_prefs, personality)
        humor_level = self._map_humor_level(comm_prefs, personality)
        
        # Check if preferences already exist
        existing_prefs = self.db_manager.execute_query(
            "SELECT id FROM dialogue_style_preferences WHERE user_id = ?",
            (user_id,)
        )
        
        if existing_prefs:
            # Update existing preferences
            success = self.db_manager.execute_update(
                """
                UPDATE dialogue_style_preferences
                SET formality_level = ?, verbosity_level = ?, empathy_level = ?, humor_level = ?, 
                    last_updated = CURRENT_TIMESTAMP
                WHERE user_id = ?
                """,
                (formality_level, verbosity_level, empathy_level, humor_level, user_id)
            ) > 0
        else:
            # Insert new preferences
            success = self.db_manager.execute_insert(
                """
                INSERT INTO dialogue_style_preferences 
                (user_id, formality_level, verbosity_level, empathy_level, humor_level)
                VALUES (?, ?, ?, ?, ?)
                """,
                (user_id, formality_level, verbosity_level, empathy_level, humor_level)
            ) > 0
        
        if success:
            logger.info(f"Updated dialogue style preferences for user {user_id}")
        else:
            logger.error(f"Failed to update dialogue style preferences for user {user_id}")
            
        return success
    
    def _map_formality_level(self, comm_prefs: Dict, personality: Dict) -> int:
        """Map communication preferences to formality level (1-5)."""
        # Default to middle level
        level = 3
        
        # Check for explicit formality preferences
        formality_indicators = comm_prefs.get('formality', '').lower()
        if 'formal' in formality_indicators or 'professional' in formality_indicators:
            level += 1
        if 'very formal' in formality_indicators or 'highly professional' in formality_indicators:
            level += 1
        if 'casual' in formality_indicators or 'informal' in formality_indicators:
            level -= 1
        if 'very casual' in formality_indicators or 'very informal' in formality_indicators:
            level -= 1
            
        # Adjust based on personality traits
        if personality.get('conscientiousness') == 'high':
            level += 1
        if personality.get('openness') == 'high':
            level -= 1
            
        # Ensure within range
        return max(1, min(5, level))
    
    def _map_verbosity_level(self, comm_prefs: Dict, personality: Dict) -> int:
        """Map communication preferences to verbosity level (1-5)."""
        # Default to middle level
        level = 3
        
        # Check for explicit verbosity preferences
        verbosity_indicators = comm_prefs.get('verbosity', '').lower()
        if 'detailed' in verbosity_indicators or 'thorough' in verbosity_indicators:
            level += 1
        if 'very detailed' in verbosity_indicators or 'comprehensive' in verbosity_indicators:
            level += 1
        if 'concise' in verbosity_indicators or 'brief' in verbosity_indicators:
            level -= 1
        if 'very concise' in verbosity_indicators or 'minimal' in verbosity_indicators:
            level -= 1
            
        # Adjust based on personality traits
        if personality.get('extraversion') == 'high':
            level += 1
        if personality.get('introversion') == 'high':
            level -= 1
            
        # Ensure within range
        return max(1, min(5, level))
    
    def _map_empathy_level(self, comm_prefs: Dict, personality: Dict) -> int:
        """Map communication preferences to empathy level (1-5)."""
        # Default to middle level
        level = 3
        
        # Check for explicit empathy preferences
        empathy_indicators = comm_prefs.get('emotional_tone', '').lower()
        if 'empathetic' in empathy_indicators or 'supportive' in empathy_indicators:
            level += 1
        if 'very empathetic' in empathy_indicators or 'highly supportive' in empathy_indicators:
            level += 1
        if 'factual' in empathy_indicators or 'objective' in empathy_indicators:
            level -= 1
        if 'very factual' in empathy_indicators or 'strictly objective' in empathy_indicators:
            level -= 1
            
        # Adjust based on personality traits
        if personality.get('agreeableness') == 'high':
            level += 1
        if personality.get('analytical') == 'high':
            level -= 1
            
        # Ensure within range
        return max(1, min(5, level))
    
    def _map_humor_level(self, comm_prefs: Dict, personality: Dict) -> int:
        """Map communication preferences to humor level (1-5)."""
        # Default to middle level
        level = 3
        
        # Check for explicit humor preferences
        humor_indicators = comm_prefs.get('humor', '').lower()
        if 'humorous' in humor_indicators or 'likes jokes' in humor_indicators:
            level += 1
        if 'very humorous' in humor_indicators or 'loves jokes' in humor_indicators:
            level += 1
        if 'serious' in humor_indicators or 'professional' in humor_indicators:
            level -= 1
        if 'very serious' in humor_indicators or 'no humor' in humor_indicators:
            level -= 1
            
        # Adjust based on personality traits
        if personality.get('playfulness') == 'high':
            level += 1
        if personality.get('seriousness') == 'high':
            level -= 1
            
        # Ensure within range
        return max(1, min(5, level))
    
    def get_psychological_profile(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve the psychological profile for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            Psychological profile data or None if not found
        """
        profile_data = self.db_manager.execute_query(
            "SELECT profile_data FROM user_psychological_profile WHERE user_id = ?",
            (user_id,)
        )
        
        if profile_data:
            try:
                return json.loads(profile_data[0]['profile_data'])
            except (json.JSONDecodeError, IndexError, KeyError) as e:
                logger.error(f"Error parsing psychological profile for user {user_id}: {e}")
                
        return None
    
    def get_dialogue_style(self, user_id: int) -> Dict[str, Any]:
        """
        Get the dialogue style preferences for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary containing dialogue style preferences
        """
        style_data = self.db_manager.execute_query(
            """
            SELECT formality_level, verbosity_level, empathy_level, humor_level
            FROM dialogue_style_preferences
            WHERE user_id = ?
            """,
            (user_id,)
        )
        
        if style_data:
            return {
                'formality_level': style_data[0]['formality_level'],
                'verbosity_level': style_data[0]['verbosity_level'],
                'empathy_level': style_data[0]['empathy_level'],
                'humor_level': style_data[0]['humor_level']
            }
        
        # Return default values if no preferences found
        return {
            'formality_level': 3,
            'verbosity_level': 3,
            'empathy_level': 3,
            'humor_level': 3
        }
    
    def generate_dialogue_with_style(self, user_id: int, prompt: str, context_id: Optional[str] = None) -> Tuple[str, str]:
        """
        Generate dialogue with adjusted style based on user psychological profile.
        
        Args:
            user_id: User ID
            prompt: Base prompt for dialogue generation
            context_id: Optional context ID for conversation grouping
            
        Returns:
            Tuple of (generated dialogue, context_id)
        """
        # Get dialogue style preferences
        style = self.get_dialogue_style(user_id)
        
        # Get conversation history for context
        history = self.get_conversation_history(user_id, limit=10, context_id=context_id)
        
        # Create a new context_id if not provided
        if not context_id:
            context_id = f"ctx_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Adjust prompt based on style preferences
        styled_prompt = self._adjust_prompt_for_style(prompt, style, history)
        
        # Call dialogue API with styled prompt
        dialogue = self._call_dialogue_api(styled_prompt)
        
        # Store the conversation
        if dialogue:
            # Store user message
            self.store_message(user_id, prompt, is_user=True, context_id=context_id)
            # Store AI response
            self.store_message(user_id, dialogue, is_user=False, context_id=context_id)
        
        return dialogue, context_id
    
    def _adjust_prompt_for_style(self, base_prompt: str, style: Dict[str, int], history: List[Dict]) -> str:
        """
        Adjust the prompt based on dialogue style preferences.
        
        Args:
            base_prompt: Base prompt for dialogue generation
            style: Dialogue style preferences
            history: Conversation history
            
        Returns:
            Adjusted prompt
        """
        # Extract style parameters
        formality = style.get('formality_level', 3)
        verbosity = style.get('verbosity_level', 3)
        empathy = style.get('empathy_level', 3)
        humor = style.get('humor_level', 3)
        
        # Create style instructions
        style_instructions = []
        
        # Formality instructions
        if formality == 1:
            style_instructions.append("使用非常随意、口语化的语气，就像与朋友聊天一样。")
        elif formality == 2:
            style_instructions.append("使用友好、轻松的语气，但保持基本礼貌。")
        elif formality == 4:
            style_instructions.append("使用较为正式的语气，注重礼节和专业性。")
        elif formality == 5:
            style_instructions.append("使用非常正式、礼貌的语气，如同专业场合的交流。")
        
        # Verbosity instructions
        if verbosity == 1:
            style_instructions.append("回答要非常简洁，尽量使用短句。")
        elif verbosity == 2:
            style_instructions.append("回答要简明扼要，避免不必要的细节。")
        elif verbosity == 4:
            style_instructions.append("回答要相对详细，提供充分的信息和解释。")
        elif verbosity == 5:
            style_instructions.append("回答要非常详尽，提供全面的信息、解释和例子。")
        
        # Empathy instructions
        if empathy == 1:
            style_instructions.append("保持客观、中立的态度，专注于事实和信息。")
        elif empathy == 2:
            style_instructions.append("主要关注事实，但也表达一定的理解。")
        elif empathy == 4:
            style_instructions.append("表现出关心和理解，积极回应用户的情感需求。")
        elif empathy == 5:
            style_instructions.append("表现出高度的同理心和情感支持，优先考虑用户的感受。")
        
        # Humor instructions
        if humor == 1:
            style_instructions.append("保持严肃的语气，避免任何幽默或轻松的表达。")
        elif humor == 2:
            style_instructions.append("主要保持严肃，偶尔可以使用轻微的幽默。")
        elif humor == 4:
            style_instructions.append("适当加入幽默元素，使对话更加轻松愉快。")
        elif humor == 5:
            style_instructions.append("积极使用幽默和俏皮的表达，让对话充满乐趣。")
        
        # Add conversation history for context
        history_text = ""
        if history:
            history_text = "以下是之前的对话历史，请参考以保持连贯性：\n"
            for msg in history:
                role = "用户" if msg['role'] == 'user' else "助手"
                history_text += f"{role}: {msg['content']}\n"
            history_text += "\n"
        
        # Combine everything into a styled prompt
        styled_prompt = f"""
        {history_text}
        在回复以下内容时，请遵循这些风格指导：
        {' '.join(style_instructions)}
        
        {base_prompt}
        """
        
        return styled_prompt
    
    def _call_dialogue_api(self, prompt: str) -> Optional[str]:
        """
        Call the dialogue generation API.
        
        Args:
            prompt: Prompt for dialogue generation
            
        Returns:
            Generated dialogue or None if API call fails
        """
        api_key = get_api_key('ZHIPUAI')
        if not api_key:
            logger.error("ZhipuAI API key not found. Cannot call dialogue API.")
            return None
        
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            "model": DEFAULT_MODEL,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,  # Moderate temperature for natural responses
            "max_tokens": 800  # Increased token limit for longer responses
        }
        
        try:
            response_data = make_api_request(ZHIPUAI_API_ENDPOINT, headers=headers, json_payload=payload)
            
            if response_data and 'choices' in response_data and response_data['choices']:
                message = response_data['choices'][0].get('message')
                if isinstance(message, dict) and 'content' in message:
                    dialogue = message['content'].strip()
                    if dialogue and dialogue != "[empty]" and dialogue != "[blank]":
                        logger.info(f"Received dialogue from API: {dialogue[:50]}...")
                        return dialogue
            
            logger.warning("Invalid or empty response from dialogue API")
            
        except Exception as e:
            logger.error(f"Error calling dialogue API: {e}")
        
        return None
