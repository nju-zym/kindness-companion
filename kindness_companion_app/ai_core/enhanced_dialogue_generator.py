"""
Enhanced dialogue generator that incorporates user psychological analysis
and maintains extended conversation context.
"""

import logging
from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime

from .dialogue_generator import generate_pet_dialogue
from .conversation_analyzer import ConversationAnalyzer

logger = logging.getLogger(__name__)


class EnhancedDialogueGenerator:
    """
    Enhanced dialogue generator that incorporates user psychological analysis
    and maintains extended conversation context.
    """

    def __init__(self, db_manager):
        """
        Initialize the enhanced dialogue generator.

        Args:
            db_manager: Database manager instance
        """
        self.db_manager = db_manager
        self.conversation_analyzer = ConversationAnalyzer(db_manager)
        self.active_contexts = {}  # Store active conversation contexts by user_id
        self.context_cleanup_interval = 24 * 60 * 60  # 24小时清理一次
        self.last_cleanup_time = datetime.now()

    def generate_dialogue(
        self, user_id: int, event_type: str, event_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate dialogue with psychological profile adaptation and extended context.

        Args:
            user_id: User ID
            event_type: Type of event triggering the dialogue
            event_data: Data associated with the event

        Returns:
            Dictionary containing dialogue and additional information
        """
        try:
            # 定期清理过期对话
            self._check_and_cleanup_old_conversations()

            # 获取活跃上下文
            context_id = self.active_contexts.get(user_id)

            # 对于用户消息，进行分析和存储
            if event_type == "user_message" and "message" in event_data:
                user_message = event_data["message"]

                # 存储用户消息到对话历史
                if not context_id:
                    context_id = f"ctx_{datetime.now().strftime('%Y%m%d%H%M%S')}"
                    self.active_contexts[user_id] = context_id

                self.conversation_analyzer.store_message(
                    user_id=user_id,
                    content=user_message,
                    is_user=True,
                    context_id=context_id,
                    topic="user_message",
                    emotion_score=0.0,
                )

                # 定期分析用户心理特征（每10条消息）
                message_count = len(
                    self.conversation_analyzer.get_conversation_history(
                        user_id, limit=1000, context_id=None
                    )
                )

                if message_count % 10 == 0:
                    logger.info(
                        f"Analyzing psychological profile for user {user_id} after {message_count} messages"
                    )
                    self.conversation_analyzer.analyze_user_psychology(user_id)

            # 构建基础提示词
            base_prompt = self._construct_base_prompt(user_id, event_type, event_data)

            # 获取对话历史作为上下文
            conversation_history = self.conversation_analyzer.get_conversation_history(
                user_id, context_id=context_id
            )

            # 生成带风格适应的对话
            dialogue, context_id = (
                self.conversation_analyzer.generate_dialogue_with_style(
                    user_id, base_prompt, context_id
                )
            )

            # 存储AI回复
            if dialogue:
                self.conversation_analyzer.store_message(
                    user_id=user_id,
                    content=dialogue,
                    is_user=False,
                    context_id=context_id,
                    topic="ai_response",
                    emotion_score=0.0,
                )

            # 更新活跃上下文
            self.active_contexts[user_id] = context_id

            # 获取用户心理特征
            profile = self.conversation_analyzer.get_psychological_profile(user_id)

            return {
                "dialogue": dialogue or "... (The pet seems lost in thought)",
                "context_id": context_id,
                "profile_available": profile is not None,
                "conversation_history": conversation_history,
                "suggested_animation": self._suggest_animation(
                    event_type, event_data, profile
                ),
            }
        except Exception as e:
            logger.error(f"Error during dialogue generation: {str(e)}")
            return {
                "dialogue": "... (The pet seems lost in thought)",
                "context_id": None,
                "profile_available": False,
                "conversation_history": [],
                "suggested_animation": "confused",
            }

    def _check_and_cleanup_old_conversations(self):
        """检查并清理过期对话"""
        current_time = datetime.now()
        if (
            current_time - self.last_cleanup_time
        ).total_seconds() >= self.context_cleanup_interval:
            self.conversation_analyzer.cleanup_old_conversations()
            self.last_cleanup_time = current_time

    def _construct_base_prompt(
        self, user_id: int, event_type: str, event_data: Dict[str, Any]
    ) -> str:
        """
        Construct a base prompt for dialogue generation.

        Args:
            user_id: User ID
            event_type: Type of event triggering the dialogue
            event_data: Data associated with the event

        Returns:
            Base prompt for dialogue generation
        """
        # 获取对话历史
        conversation_history = self.conversation_analyzer.get_conversation_history(
            user_id, limit=10, context_id=self.active_contexts.get(user_id)
        )

        # 构建基础提示词
        prompt_parts = [
            "你是'Kai'，善行伴侣应用中友好、乐观且略带好奇的虚拟宠物。",
            "你的目标是鼓励用户并让他们感到被支持。",
            "保持回应简洁（1-2句话），温暖自然，像真正的伙伴一样。",
            "避免空洞的套话。尝试与具体事件建立联系。",
            f"用户（ID: {user_id}）刚刚触发了一个事件：'{event_type}'。",
        ]

        # 添加对话历史上下文
        if conversation_history:
            prompt_parts.append("\n以下是最近的对话历史，请参考以保持连贯性：")
            for msg in conversation_history[-5:]:  # 只使用最近5条消息
                role = "用户" if msg["role"] == "user" else "你"
                prompt_parts.append(f"{role}: {msg['content']}")

        # 添加事件特定上下文
        if event_type == "check_in":
            if "challenge_title" in event_data:
                prompt_parts.append(
                    f"他们刚刚为挑战\"{event_data['challenge_title']}\"打卡。表示赞赏并鼓励他们继续。"
                )
            else:
                prompt_parts.append("他们刚刚完成了一次打卡。表示赞赏并鼓励他们继续。")

            if "streak" in event_data:
                streak = event_data["streak"]
                if streak > 1:
                    prompt_parts.append(
                        f"这是他们连续第{streak}天完成这个挑战。表示赞赏他们的坚持。"
                    )

        elif event_type == "reflection_added":
            if "text" in event_data and event_data["text"]:
                prompt_parts.append(f"他们添加了一条反思：\"{event_data['text']}\"。")
                prompt_parts.append(
                    "你可以温和地提出一个开放式问题，询问他们的体验，但不要强迫。"
                )
            else:
                prompt_parts.append(
                    "他们添加了一条反思（内容未显示）。肯定他们的努力。"
                )

        elif event_type == "app_opened":
            prompt_parts.append(
                "用户刚刚打开了应用。热情地问候他们，也许可以为这一天提供一些温和的鼓励。"
            )

        elif event_type == "user_message":
            if "message" in event_data and event_data["message"]:
                prompt_parts.append(
                    f"用户向你发送了一条消息：\"{event_data['message']}\"。直接且有吸引力地回应他们的消息。"
                )
                if "analyzed_emotion" in event_data:
                    prompt_parts.append(
                        f"他们的消息似乎带有'{event_data['analyzed_emotion']}'的语气。调整你的回应。"
                    )
            else:
                prompt_parts.append("用户发送了一条空消息。也许问问他们是否一切都好？")

        # 添加最终指令
        prompt_parts.append("\n现在生成你的回应:")

        return "\n".join(prompt_parts)

    def _suggest_animation(
        self,
        event_type: str,
        event_data: Dict[str, Any],
        profile: Optional[Dict[str, Any]],
    ) -> str:
        """
        Suggest an animation based on event type, event data, and user profile.

        Args:
            event_type: Type of event triggering the dialogue
            event_data: Data associated with the event
            profile: User psychological profile

        Returns:
            Suggested animation name
        """
        # If suggested_animation is already provided in event_data, use it
        if "suggested_animation" in event_data:
            return event_data["suggested_animation"]

        # Default animation
        animation = "idle"

        # Event-based animations (basic logic)
        if event_type == "check_in":
            animation = "happy"  # Simple positive feedback for check-in

        elif event_type == "user_message" or event_type == "reflection_added":
            # For user messages and reflections, base animation on detected emotion
            emotion = event_data.get("analyzed_emotion", "").lower()

            # Map detailed emotions to animations
            if emotion in ["happy", "content", "grateful", "optimistic"]:
                animation = "happy"
            elif emotion in ["excited", "joyful", "proud"]:
                animation = "excited"
            elif emotion in [
                "sad",
                "anxious",
                "worried",
                "frustrated",
                "angry",
                "disappointed",
                "stressed",
                "negative",
            ]:
                animation = "concerned"
            elif emotion in ["surprised", "confused", "uncertain"]:
                animation = "confused"
            elif emotion in ["calm", "reflective", "curious", "neutral"]:
                animation = "idle"
            elif emotion == "positive":
                animation = "happy"
            else:
                # Default animations based on event type
                animation = "happy" if event_type == "user_message" else "idle"

        # Profile-based animation adjustments
        if profile:
            personality = profile.get("personality_traits", {})

            # Adjust animations based on user personality traits
            if personality:
                # If user tends to be more serious, tone down excitement
                if personality.get("seriousness") == "high" and animation == "excited":
                    animation = "happy"

                # If user tends to be more sensitive, increase empathy for concerned animations
                if (
                    personality.get("sensitivity") == "high"
                    and animation == "concerned"
                ):
                    # We keep 'concerned' but might add more nuanced animations in the future
                    pass

                # If user tends to be more playful, increase excitement for happy animations
                if personality.get("playfulness") == "high" and animation == "happy":
                    animation = "excited"

                # If user tends to be more anxious, show more concerned animations
                if personality.get("anxiety") == "high" and animation == "idle":
                    animation = "concerned"

        # Ensure we're returning a valid animation that exists in our resources
        valid_animations = ["idle", "happy", "excited", "concerned", "confused"]
        if animation not in valid_animations:
            logger.warning(
                f"Invalid animation suggested: {animation}. Falling back to 'idle'."
            )
            animation = "idle"

        return animation

    def reset_context(self, user_id: int) -> None:
        """
        Reset the conversation context for a user.

        Args:
            user_id: User ID
        """
        if user_id in self.active_contexts:
            del self.active_contexts[user_id]
            logger.info(f"Reset conversation context for user {user_id}")

    def get_active_context(self, user_id: int) -> Optional[str]:
        """
        Get the active conversation context for a user.

        Args:
            user_id: User ID

        Returns:
            Context ID or None if no active context
        """
        return self.active_contexts.get(user_id)
