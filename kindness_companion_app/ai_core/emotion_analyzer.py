import logging
from typing import Optional, Dict, Tuple, List, Callable, NamedTuple
import os
import requests
from requests.exceptions import RequestException
import threading
import queue
import time
import json
import math
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

# API configuration
ZHIPUAI_API_ENDPOINT = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
DEFAULT_MODEL = "glm-4-flash"


# 基于Russell核心情感理论的维度模型
@dataclass
class EmotionDimensions:
    """Russell核心情感理论的三维模型"""

    valence: float  # 愉悦度 (-1.0 到 1.0, -1最不愉快, 1最愉快)
    arousal: float  # 唤醒度 (-1.0 到 1.0, -1最低唤醒, 1最高唤醒)
    dominance: float  # 控制度 (-1.0 到 1.0, -1最无控制感, 1最有控制感)


# 基于Plutchik情感轮的八种基础情感
class PlutchikEmotions(Enum):
    """Plutchik情感轮的八种基础情感"""

    JOY = "joy"  # 快乐
    TRUST = "trust"  # 信任
    FEAR = "fear"  # 恐惧
    SURPRISE = "surprise"  # 惊讶
    SADNESS = "sadness"  # 悲伤
    DISGUST = "disgust"  # 厌恶
    ANGER = "anger"  # 愤怒
    ANTICIPATION = "anticipation"  # 期待


# Plutchik情感的强度级别
class EmotionIntensity(Enum):
    """情感强度级别"""

    LOW = 1  # 低强度
    MEDIUM = 2  # 中等强度
    HIGH = 3  # 高强度


@dataclass
class EmotionState:
    """完整的情感状态表示"""

    primary_emotion: PlutchikEmotions
    intensity: EmotionIntensity
    dimensions: EmotionDimensions
    secondary_emotions: List[Tuple[PlutchikEmotions, float]]  # 次要情感及其权重
    confidence: float  # 分析置信度 (0.0-1.0)
    _special_animation: Optional[str] = None  # 特殊动画状态

    def to_animation_state(self) -> str:
        """
        智能转换为动画状态
        考虑主要情感、强度、维度信息和次要情感
        """
        try:
            # 0. 检查是否有特殊动画状态
            if hasattr(self, "_special_animation") and self._special_animation:
                return self._special_animation

            # 1. 获取基础动画（基于主要情感和强度）
            base_animation = EMOTION_ANIMATION_MAPPING[self.primary_emotion][
                self.intensity
            ]

            # 2. 基于维度信息进行调节
            adjusted_animation = self._adjust_animation_by_dimensions(base_animation)

            # 3. 考虑次要情感的影响
            final_animation = self._consider_secondary_emotions(adjusted_animation)

            # 4. 确保动画状态有效
            if final_animation not in ANIMATION_STATES:
                logger.warning(
                    f"无效的动画状态: {final_animation}, 回退到基础动画: {base_animation}"
                )
                return base_animation if base_animation in ANIMATION_STATES else "idle"

            return final_animation

        except (KeyError, AttributeError) as e:
            logger.error(f"动画状态转换失败: {e}")
            return "idle"  # 安全回退

    def _adjust_animation_by_dimensions(self, base_animation: str) -> str:
        """基于Russell维度理论调节动画"""
        # 分析维度特征
        arousal_level = (
            "high_arousal" if self.dimensions.arousal > 0.4 else "low_arousal"
        )
        valence_level = (
            "positive_valence" if self.dimensions.valence > 0.1 else "negative_valence"
        )
        dominance_level = (
            "high_dominance" if self.dimensions.dominance > 0.2 else "low_dominance"
        )

        # 对于某些特定情感，不应用维度调节
        primary_emotion = self.primary_emotion
        if primary_emotion == PlutchikEmotions.SURPRISE:
            # surprise应该始终保持confused，不受维度影响
            return base_animation
        elif primary_emotion in [PlutchikEmotions.JOY, PlutchikEmotions.ANTICIPATION]:
            # joy和anticipation应该保持积极，只在确实是负面维度时才调节
            if self.dimensions.valence < -0.3:  # 只有明显负面时才调节
                pass  # 允许调节
            else:
                return base_animation  # 保持原有的积极动画

        # 检查维度组合调节规则
        for (
            dimension_combo,
            suggested_animation,
        ) in DIMENSION_ANIMATION_ADJUSTMENTS.items():
            if len(dimension_combo) == 2:
                # 双维度规则
                if (
                    arousal_level in dimension_combo
                    and valence_level in dimension_combo
                ):
                    return suggested_animation
            elif len(dimension_combo) == 1:
                # 单维度规则
                if dominance_level in dimension_combo:
                    return suggested_animation

        return base_animation

    def _consider_secondary_emotions(self, current_animation: str) -> str:
        """考虑次要情感对动画的影响"""
        if not self.secondary_emotions:
            return current_animation

        # 如果有强烈的次要情感，可能需要调节动画
        for secondary_emotion, weight in self.secondary_emotions:
            if weight > 0.6:  # 权重较高的次要情感
                # 如果次要情感与主要情感冲突，选择更中性的动画
                secondary_animation = EMOTION_ANIMATION_MAPPING[secondary_emotion][
                    self.intensity
                ]
                if secondary_animation != current_animation:
                    # 冲突时选择更中性的动画
                    if (
                        current_animation == "excited"
                        and secondary_animation == "concerned"
                    ):
                        return "confused"
                    elif (
                        current_animation == "happy"
                        and secondary_animation == "concerned"
                    ):
                        return "idle"

        return current_animation


# 基于Plutchik理论的精细化情感到动画映射
EMOTION_ANIMATION_MAPPING = {
    # 主要情感的基础动画
    PlutchikEmotions.JOY: {
        EmotionIntensity.LOW: "happy",
        EmotionIntensity.MEDIUM: "happy",
        EmotionIntensity.HIGH: "excited",
    },
    PlutchikEmotions.TRUST: {
        EmotionIntensity.LOW: "happy",  # 信任应该是积极的，即使是低强度
        EmotionIntensity.MEDIUM: "happy",
        EmotionIntensity.HIGH: "happy",
    },
    PlutchikEmotions.FEAR: {
        EmotionIntensity.LOW: "concerned",
        EmotionIntensity.MEDIUM: "concerned",
        EmotionIntensity.HIGH: "concerned",
    },
    PlutchikEmotions.SURPRISE: {
        EmotionIntensity.LOW: "confused",
        EmotionIntensity.MEDIUM: "confused",
        EmotionIntensity.HIGH: "confused",  # 高强度惊讶仍然是困惑，不是兴奋
    },
    PlutchikEmotions.SADNESS: {
        EmotionIntensity.LOW: "concerned",
        EmotionIntensity.MEDIUM: "concerned",
        EmotionIntensity.HIGH: "concerned",
    },
    PlutchikEmotions.DISGUST: {
        EmotionIntensity.LOW: "concerned",
        EmotionIntensity.MEDIUM: "concerned",
        EmotionIntensity.HIGH: "concerned",
    },
    PlutchikEmotions.ANGER: {
        EmotionIntensity.LOW: "concerned",
        EmotionIntensity.MEDIUM: "concerned",
        EmotionIntensity.HIGH: "concerned",
    },
    PlutchikEmotions.ANTICIPATION: {
        EmotionIntensity.LOW: "happy",  # 期待应该是积极的
        EmotionIntensity.MEDIUM: "excited",
        EmotionIntensity.HIGH: "excited",
    },
}

# 基于维度的动画调节规则
DIMENSION_ANIMATION_ADJUSTMENTS = {
    # 高唤醒度 + 正愉悦度 = 兴奋表现
    ("high_arousal", "positive_valence"): "excited",
    # 高唤醒度 + 负愉悦度 = 担忧表现
    ("high_arousal", "negative_valence"): "concerned",
    # 低唤醒度 + 正愉悦度 = 平静开心
    ("low_arousal", "positive_valence"): "happy",
    # 低唤醒度 + 负愉悦度 = 沮丧表现
    ("low_arousal", "negative_valence"): "concerned",
    # 低控制感总是表现担忧
    ("low_dominance",): "concerned",
    # 高控制感倾向积极表现
    ("high_dominance",): "happy",
}

# Animation states - 扩展动画状态定义
ANIMATION_STATES = {
    "thinking": "thinking",
    "idle": "idle",
    "happy": "happy",
    "concerned": "concerned",
    "confused": "confused",
    "excited": "excited",
}

# 为每种动画状态配置合适的文字提示
ANIMATION_TEXT_PROMPTS = {
    "thinking": [
        "让我想想...",
        "嗯，我在思考你说的话...",
        "我正在仔细考虑这个问题...",
        "给我一点时间思考一下...",
        "我需要好好想想这个...",
        "让我分析一下你的想法...",
        "这很有趣，让我想想...",
        "我在琢磨你的意思...",
    ],
    "idle": [
        "我在这里陪着你呢~",
        "有什么想聊的吗？",
        "我在静静地听着...",
        "我会一直陪伴在你身边",
        "随时可以和我说话哦",
        "我在这里等你...",
        "有什么需要帮助的吗？",
        "我们可以慢慢聊~",
    ],
    "happy": [
        "这真是太好了！",
        "我为你感到开心呢~",
        "听起来真不错呀！",
        "这让我也觉得很愉快！",
        "真是个好消息！",
        "我能感受到你的快乐~",
        "这样的好事值得庆祝！",
        "你的开心也感染了我呢！",
        "这真的很棒！",
        "我替你高兴！",
    ],
    "concerned": [
        "我有点担心你呢...",
        "听起来你似乎有些困扰？",
        "我能理解你的感受...",
        "这确实是令人担忧的事情",
        "我想为你分担一些担忧",
        "你现在还好吗？",
        "我会陪着你度过难关的",
        "如果你需要倾诉，我在这里",
        "我关心你的感受...",
        "让我们一起面对这个问题",
    ],
    "confused": [
        "咦？这是什么意思呀？",
        "我有点不太明白...",
        "能再解释一下吗？",
        "这让我感到有些困惑呢",
        "我需要理解得更清楚一些",
        "这个...我还没太懂呢",
        "你能说得详细一点吗？",
        "我好像跟不上你的思路了",
        "这有点超出我的理解了",
        "能帮我澄清一下吗？",
    ],
    "excited": [
        "哇！这太令人兴奋了！",
        "太棒了！我都激动起来了！",
        "这真是太赞了！",
        "我和你一样兴奋呢！",
        "这简直太精彩了！",
        "我都忍不住要为你欢呼了！",
        "这种感觉真是太好了！",
        "太厉害了！我都被感染了！",
        "这让我充满了活力！",
        "真是太令人振奋了！",
    ],
}

# 根据情感强度调整文字提示的词典
INTENSITY_TEXT_MODIFIERS = {
    EmotionIntensity.LOW: {
        "happy": ["还不错呢~", "挺好的~", "听起来还可以", "这样挺好的"],
        "concerned": ["稍微有点担心", "有一点点担忧", "似乎有些不太对"],
        "excited": ["有点小兴奋呢", "听起来不错", "还挺有意思的"],
    },
    EmotionIntensity.MEDIUM: {
        "happy": ["真的很不错！", "这很好呀！", "听起来很棒！"],
        "concerned": ["我有些担心", "这确实让人忧虑", "我能理解你的困扰"],
        "excited": ["太好了！", "真不错！", "这很令人兴奋！"],
    },
    EmotionIntensity.HIGH: {
        "happy": ["太棒了！", "这简直太好了！", "我为你感到超级开心！"],
        "concerned": ["我非常担心你", "这真的很令人担忧", "我们必须重视这个问题"],
        "excited": ["哇！太令人兴奋了！", "这简直太赞了！", "我都激动得不行了！"],
    },
}

# 基于用户情感历史的个性化文字提示
CONTEXTUAL_TEXT_PROMPTS = {
    "first_interaction": [
        "很高兴认识你！",
        "欢迎来找我聊天~",
        "我很期待和你的交流！",
    ],
    "frequent_positive": [
        "你总是能带给我正能量呢！",
        "和你聊天真的很愉快~",
        "你的乐观态度很感染人！",
    ],
    "frequent_negative": [
        "我会一直陪伴着你的",
        "无论遇到什么，我都在这里",
        "我们一起慢慢来，不着急",
    ],
    "mood_improvement": [
        "看到你心情变好，我也很开心！",
        "你的状态越来越好了呢~",
        "感觉你今天比之前更开朗了！",
    ],
    "emotional_volatility": [
        "我注意到你的情绪有些波动",
        "无论你现在什么感受，我都理解",
        "情绪起伏是很正常的，我陪着你",
    ],
}

# 动画过渡兼容性矩阵（定义哪些动画之间可以直接切换）
ANIMATION_TRANSITIONS = {
    "idle": ["happy", "concerned", "confused", "excited", "thinking"],
    "happy": ["excited", "idle", "confused"],
    "excited": ["happy", "confused", "idle"],
    "concerned": ["idle", "confused"],
    "confused": ["idle", "happy", "excited", "concerned"],
    "thinking": ["idle", "happy", "concerned", "confused", "excited"],
}

# Plutchik情感轮的维度映射
PLUTCHIK_DIMENSIONS = {
    PlutchikEmotions.JOY: EmotionDimensions(valence=0.8, arousal=0.6, dominance=0.5),
    PlutchikEmotions.TRUST: EmotionDimensions(valence=0.6, arousal=0.2, dominance=0.3),
    PlutchikEmotions.FEAR: EmotionDimensions(valence=-0.7, arousal=0.8, dominance=-0.8),
    PlutchikEmotions.SURPRISE: EmotionDimensions(
        valence=0.0, arousal=0.9, dominance=-0.2
    ),
    PlutchikEmotions.SADNESS: EmotionDimensions(
        valence=-0.8, arousal=-0.4, dominance=-0.6
    ),
    PlutchikEmotions.DISGUST: EmotionDimensions(
        valence=-0.7, arousal=0.3, dominance=0.2
    ),
    PlutchikEmotions.ANGER: EmotionDimensions(valence=-0.6, arousal=0.7, dominance=0.6),
    PlutchikEmotions.ANTICIPATION: EmotionDimensions(
        valence=0.3, arousal=0.5, dominance=0.4
    ),
}

# 中文情感关键词映射到Plutchik情感
CHINESE_EMOTION_KEYWORDS = {
    PlutchikEmotions.JOY: [
        "开心",
        "快乐",
        "高兴",
        "愉快",
        "兴奋",
        "喜悦",
        "棒",
        "赞",
        "幸福",
        "满足",
        "满分",
        "成功",
        "胜利",
        "赢了",
        "通过",
        "及格",
        "优秀",
        "完美",
        "太好了",
        "厉害",
        "牛",
        "不错",
        "不坏",
        "不差",
        "不赖",
        "还行",
        "还好",
        "挺好",
        "蛮好",
        "很好",
        "真好",
        "良好",
        "舒服",
        "舒心",
        "美好",
        "wonderful",
        "amazing",
        "wonderful",
        "great",
        "excellent",
        "perfect",
        "good",
        "nice",
        "fine",
    ],
    PlutchikEmotions.TRUST: ["信任", "依赖", "相信", "放心", "安心", "可靠", "踏实"],
    PlutchikEmotions.FEAR: [
        "害怕",
        "恐惧",
        "担心",
        "紧张",
        "不安",
        "焦虑",
        "惊慌",
        "担忧",
    ],
    PlutchikEmotions.SURPRISE: ["惊讶", "意外", "震惊", "诧异", "吃惊", "惊奇", "哇"],
    PlutchikEmotions.SADNESS: [
        "难过",
        "伤心",
        "悲伤",
        "不开心",
        "沮丧",
        "失望",
        "痛苦",
        "难受",
    ],
    PlutchikEmotions.DISGUST: ["恶心", "讨厌", "厌恶", "反感", "恶心", "排斥"],
    PlutchikEmotions.ANGER: [
        "生气",
        "愤怒",
        "恼火",
        "烦躁",
        "不满",
        "不爽",
        "气愤",
        "恼怒",
    ],
    PlutchikEmotions.ANTICIPATION: [
        "期待",
        "盼望",
        "希望",
        "想要",
        "渴望",
        "期盼",
        "憧憬",
        "即将",
        "马上",
        "快要",
    ],
}


class EmotionAnalyzer:
    """基于科学理论的情感分析器"""

    def __init__(self):
        self.api_key = self._get_api_key()
        self.emotion_history: Dict[int, List[EmotionState]] = {}  # 用户情感历史
        self.animation_history: Dict[int, List[str]] = {}  # 用户动画历史
        self.current_animation: Dict[int, str] = {}  # 用户当前动画状态

    def _get_api_key(self) -> Optional[str]:
        """获取API密钥"""
        return os.getenv("ZHIPUAI_API_KEY")

    def analyze_emotion_advanced(
        self,
        text: str,
        user_id: Optional[int] = None,
        context: Optional[List[str]] = None,
    ) -> EmotionState:
        """
        基于Russell维度理论和Plutchik情感轮的高级情感分析

        Args:
            text: 待分析文本
            user_id: 用户ID，用于情感历史追踪
            context: 对话上下文

        Returns:
            EmotionState: 完整的情感状态
        """
        try:
            # 0. 首先检查特殊文本类型
            special_animation = self._detect_special_text_types(text)
            if special_animation:
                # 为特殊文本类型创建一个简化的情感状态
                emotion_state = EmotionState(
                    primary_emotion=PlutchikEmotions.TRUST,  # 中性的默认情感
                    intensity=EmotionIntensity.MEDIUM,
                    dimensions=EmotionDimensions(0.0, 0.0, 0.0),  # 中性维度
                    secondary_emotions=[],
                    confidence=0.8,  # 特殊类型的置信度较高
                )

                # 直接设置动画状态而不通过复杂的映射
                emotion_state._special_animation = special_animation

                # 应用情感上下文调整
                emotion_state = self._apply_emotional_context(emotion_state, user_id)

                # 更新用户情感历史
                if user_id:
                    self._update_emotion_history(user_id, emotion_state)

                logger.info(f"检测到特殊文本类型: {special_animation}")
                return emotion_state

            # 1. 多维度情感分析
            dimensions = self._analyze_emotion_dimensions(text, context)

            # 2. Plutchik基础情感识别
            primary_emotion, intensity = self._identify_plutchik_emotion(
                text, dimensions
            )

            # 3. 次要情感识别
            secondary_emotions = self._identify_secondary_emotions(
                text, primary_emotion
            )

            # 4. 置信度计算
            confidence = self._calculate_confidence(text, primary_emotion, dimensions)

            # 5. 构建情感状态
            emotion_state = EmotionState(
                primary_emotion=primary_emotion,
                intensity=intensity,
                dimensions=dimensions,
                secondary_emotions=secondary_emotions,
                confidence=confidence,
            )

            # 6. 应用情感上下文调整
            emotion_state = self._apply_emotional_context(emotion_state, user_id)

            # 7. 更新用户情感历史
            if user_id:
                self._update_emotion_history(user_id, emotion_state)

            logger.info(
                f"情感分析完成: {primary_emotion.value} (强度: {intensity.value}, 置信度: {confidence:.2f})"
            )
            return emotion_state

        except Exception as e:
            logger.error(f"高级情感分析失败: {e}")
            # 返回默认的中性情感状态
            return EmotionState(
                primary_emotion=PlutchikEmotions.TRUST,
                intensity=EmotionIntensity.LOW,
                dimensions=EmotionDimensions(0.0, 0.0, 0.0),
                secondary_emotions=[],
                confidence=0.1,
            )

    def _analyze_emotion_dimensions(
        self, text: str, context: Optional[List[str]] = None
    ) -> EmotionDimensions:
        """基于Russell核心情感理论分析情感维度"""

        if self.api_key:
            try:
                # 使用AI API进行维度分析
                return self._api_dimension_analysis(text, context)
            except Exception as e:
                logger.warning(f"API维度分析失败，使用关键词分析: {e}")

        # 关键词基础的维度分析
        return self._keyword_dimension_analysis(text)

    def _api_dimension_analysis(
        self, text: str, context: Optional[List[str]] = None
    ) -> EmotionDimensions:
        """使用AI API进行维度分析"""

        system_prompt = """你是基于Russell核心情感理论的专业情感分析师。
        请分析文本在以下三个维度上的得分（-1.0到1.0）：
        1. Valence (愉悦度): -1.0(极不愉快) 到 1.0(极愉快)
        2. Arousal (唤醒度): -1.0(极低唤醒/平静) 到 1.0(极高唤醒/兴奋)
        3. Dominance (控制度): -1.0(无控制感/被动) 到 1.0(强控制感/主动)

        请只返回JSON格式: {"valence": 数值, "arousal": 数值, "dominance": 数值}"""

        context_text = ""
        if context:
            context_text = f"对话上下文：{' '.join(context[-3:])}\n"

        prompt = f"""{context_text}
        分析文本："{text}"

        基于Russell核心情感理论的三维度评分："""

        response = self._call_api(prompt, system_prompt)
        if response:
            try:
                dimensions_data = json.loads(response)
                return EmotionDimensions(
                    valence=max(
                        -1.0, min(1.0, float(dimensions_data.get("valence", 0.0)))
                    ),
                    arousal=max(
                        -1.0, min(1.0, float(dimensions_data.get("arousal", 0.0)))
                    ),
                    dominance=max(
                        -1.0, min(1.0, float(dimensions_data.get("dominance", 0.0)))
                    ),
                )
            except (json.JSONDecodeError, ValueError, KeyError) as e:
                logger.warning(f"API维度响应解析失败: {e}")

        # API失败时的备用分析
        return self._keyword_dimension_analysis(text)

    def _keyword_dimension_analysis(self, text: str) -> EmotionDimensions:
        """基于关键词的维度分析"""
        text_lower = text.lower()

        # 初始化维度得分
        valence_score = 0.0
        arousal_score = 0.0
        dominance_score = 0.0

        # 扩展的愉悦度关键词
        positive_words = [
            "开心",
            "快乐",
            "高兴",
            "愉快",
            "喜悦",
            "满意",
            "棒",
            "好",
            "很好",
            "不错",
            "不坏",
            "不差",
            "不赖",
            "还行",
            "还好",
            "挺好",
            "蛮好",
            "真好",
            "良好",
            "美好",
            "顺利",
            "成功",
            "满足",
            "幸福",
            "兴奋",
            "期待",
            "希望",
            "信心",
            "积极",
            "正面",
            "乐观",
            "舒服",
            "舒心",
            "放心",
            "安心",
            "感谢",
            "赞",
        ]
        negative_words = [
            "难过",
            "伤心",
            "痛苦",
            "失望",
            "沮丧",
            "糟糕",
            "差",
            "不好",
            "担心",
            "焦虑",
            "害怕",
            "恐惧",
            "紧张",
            "不安",
            "失落",
            "绝望",
            "愤怒",
            "生气",
            "讨厌",
            "厌恶",
            "反感",
            "无助",
            "疲惫",
            "压力",
        ]

        # 扩展的唤醒度关键词
        high_arousal_words = [
            "兴奋",
            "激动",
            "紧张",
            "焦虑",
            "愤怒",
            "害怕",
            "震惊",
            "惊讶",
            "急",
            "忙",
            "激烈",
            "强烈",
            "剧烈",
            "猛烈",
            "疯狂",
            "狂热",
            "冲动",
            "热情",
            "热烈",
            "火热",
            "沸腾",
            "澎湃",
        ]
        low_arousal_words = [
            "平静",
            "放松",
            "疲惫",
            "困倦",
            "安静",
            "淡定",
            "冷静",
            "宁静",
            "安详",
            "悠闲",
            "慢",
            "缓",
            "轻松",
            "舒缓",
            "温和",
            "柔和",
            "平和",
            "恬静",
            "安逸",
            "惬意",
        ]

        # 扩展的控制度关键词
        high_dominance_words = [
            "控制",
            "决定",
            "主动",
            "自信",
            "强大",
            "能够",
            "可以",
            "确定",
            "肯定",
            "坚定",
            "果断",
            "坚强",
            "有力",
            "掌控",
            "管理",
            "指挥",
            "领导",
            "支配",
            "影响",
            "改变",
            "创造",
            "实现",
        ]
        low_dominance_words = [
            "无助",
            "被动",
            "依赖",
            "脆弱",
            "不能",
            "没办法",
            "无奈",
            "无力",
            "迷茫",
            "困惑",
            "迷失",
            "不知所措",
            "听从",
            "服从",
            "顺从",
            "屈服",
            "妥协",
            "让步",
            "退缩",
            "逃避",
            "躲避",
        ]

        # 计算维度得分 - 使用更精确的权重
        word_count = 0
        for word in positive_words:
            if word in text_lower:
                valence_score += 0.4  # 增加权重
                word_count += 1
        for word in negative_words:
            if word in text_lower:
                valence_score -= 0.4  # 增加权重
                word_count += 1

        for word in high_arousal_words:
            if word in text_lower:
                arousal_score += 0.4  # 增加权重
                word_count += 1
        for word in low_arousal_words:
            if word in text_lower:
                arousal_score -= 0.4  # 增加权重
                word_count += 1

        for word in high_dominance_words:
            if word in text_lower:
                dominance_score += 0.4  # 增加权重
                word_count += 1
        for word in low_dominance_words:
            if word in text_lower:
                dominance_score -= 0.4  # 增加权重
                word_count += 1

        # 基于文本整体语调进行调整
        # 检查感叹号和问号
        if "!" in text or "！" in text:
            arousal_score += 0.2  # 感叹号增加唤醒度
        if "?" in text or "？" in text:
            dominance_score -= 0.1  # 问号降低控制感

        # 检查否定词 - 优化逻辑，避免误处理积极短语
        negative_indicators = ["不", "没", "无", "非", "未", "别", "勿"]
        positive_phrases_with_negation = [
            "不错",
            "不坏",
            "不差",
            "不赖",
        ]  # 包含否定词但表达积极的短语

        # 先检查是否包含积极的否定短语
        has_positive_negation = any(
            phrase in text_lower for phrase in positive_phrases_with_negation
        )

        if not has_positive_negation:  # 只有在没有积极否定短语时才处理否定词
            for neg in negative_indicators:
                if neg in text_lower:
                    valence_score -= 0.1
                    dominance_score -= 0.1

        # 归一化到[-1, 1]范围
        return EmotionDimensions(
            valence=max(-1.0, min(1.0, valence_score)),
            arousal=max(-1.0, min(1.0, arousal_score)),
            dominance=max(-1.0, min(1.0, dominance_score)),
        )

    def _identify_plutchik_emotion(
        self, text: str, dimensions: EmotionDimensions
    ) -> Tuple[PlutchikEmotions, EmotionIntensity]:
        """基于Plutchik情感轮识别基础情感"""

        # 首先尝试关键词匹配
        keyword_emotion = self._keyword_plutchik_match(text)
        if keyword_emotion:
            # 根据维度强度确定情感强度
            base_intensity = self._calculate_intensity_from_dimensions(dimensions)
            # 使用关键词调整强度
            intensity = self._adjust_intensity_by_keywords(
                text, base_intensity, keyword_emotion
            )
            return keyword_emotion, intensity

        # 基于维度映射到最接近的Plutchik情感
        best_emotion = PlutchikEmotions.TRUST  # 默认情感
        best_distance = float("inf")

        for emotion, emotion_dims in PLUTCHIK_DIMENSIONS.items():
            # 计算欧氏距离
            distance = math.sqrt(
                (dimensions.valence - emotion_dims.valence) ** 2
                + (dimensions.arousal - emotion_dims.arousal) ** 2
                + (dimensions.dominance - emotion_dims.dominance) ** 2
            )

            if distance < best_distance:
                best_distance = distance
                best_emotion = emotion

        # 计算强度
        base_intensity = self._calculate_intensity_from_dimensions(dimensions)
        intensity = self._adjust_intensity_by_keywords(
            text, base_intensity, best_emotion
        )

        return best_emotion, intensity

    def _keyword_plutchik_match(self, text: str) -> Optional[PlutchikEmotions]:
        """基于关键词匹配Plutchik情感"""
        text_lower = text.lower()

        emotion_scores = {}

        for emotion, keywords in CHINESE_EMOTION_KEYWORDS.items():
            score = 0
            for keyword in keywords:
                if keyword in text_lower:
                    score += 1
            if score > 0:
                emotion_scores[emotion] = score

        if emotion_scores:
            return max(emotion_scores.items(), key=lambda x: x[1])[0]

        return None

    def _calculate_intensity_from_dimensions(
        self, dimensions: EmotionDimensions
    ) -> EmotionIntensity:
        """根据维度计算情感强度"""
        # 计算维度向量的模长作为强度指标
        magnitude = math.sqrt(
            dimensions.valence**2 + dimensions.arousal**2 + dimensions.dominance**2
        )

        if magnitude < 0.5:
            return EmotionIntensity.LOW
        elif magnitude < 1.0:
            return EmotionIntensity.MEDIUM
        else:
            return EmotionIntensity.HIGH

    def _adjust_intensity_by_keywords(
        self, text: str, base_intensity: EmotionIntensity, emotion: PlutchikEmotions
    ) -> EmotionIntensity:
        """基于关键词调整情感强度"""
        text_lower = text.lower()

        # 超高强度指示词（直接提升到HIGH）
        super_high_words = [
            "满分",
            "完美",
            "perfect",
            "amazing",
            "excellent",
            "太棒了",
            "厉害",
        ]

        # 高强度指示词
        high_intensity_words = [
            "非常",
            "特别",
            "超级",
            "极其",
            "太",
            "超",
            "最",
            "真的",
            "好",
            "很",
        ]

        # 低强度指示词
        low_intensity_words = ["有点", "稍微", "一点", "轻微", "略", "还好", "还行"]

        # 检查超高强度词汇
        super_high_count = sum(1 for word in super_high_words if word in text_lower)
        high_count = sum(1 for word in high_intensity_words if word in text_lower)
        low_count = sum(1 for word in low_intensity_words if word in text_lower)

        # 感叹号也增加强度
        exclamation_count = text.count("!") + text.count("！")
        if exclamation_count > 0:
            high_count += exclamation_count

        # 基于词汇调整强度
        if super_high_count > 0:
            # 有超高强度词汇，直接设为HIGH
            return EmotionIntensity.HIGH
        elif high_count > low_count and high_count > 0:
            # 有更多高强度词汇
            if base_intensity == EmotionIntensity.LOW:
                return EmotionIntensity.MEDIUM
            elif base_intensity == EmotionIntensity.MEDIUM:
                return EmotionIntensity.HIGH
            else:
                return EmotionIntensity.HIGH
        elif low_count > high_count:
            # 有更多低强度词汇
            if base_intensity == EmotionIntensity.HIGH:
                return EmotionIntensity.MEDIUM
            elif base_intensity == EmotionIntensity.MEDIUM:
                return EmotionIntensity.LOW
            else:
                return EmotionIntensity.LOW

        return base_intensity

    def _identify_secondary_emotions(
        self, text: str, primary_emotion: PlutchikEmotions
    ) -> List[Tuple[PlutchikEmotions, float]]:
        """识别次要情感（混合情感）"""
        text_lower = text.lower()
        secondary_emotions = []

        for emotion, keywords in CHINESE_EMOTION_KEYWORDS.items():
            if emotion == primary_emotion:
                continue

            score = 0
            for keyword in keywords:
                if keyword in text_lower:
                    score += 1

            if score > 0:
                # 计算相对权重
                weight = min(1.0, score * 0.3)
                secondary_emotions.append((emotion, weight))

        # 按权重排序，最多返回2个次要情感
        secondary_emotions.sort(key=lambda x: x[1], reverse=True)
        return secondary_emotions[:2]

    def _calculate_confidence(
        self, text: str, emotion: PlutchikEmotions, dimensions: EmotionDimensions
    ) -> float:
        """计算分析置信度"""
        confidence = 0.5  # 基础置信度

        # 基于关键词匹配增加置信度
        keyword_match = self._keyword_plutchik_match(text)
        if keyword_match == emotion:
            confidence += 0.3

        # 基于维度强度调整置信度
        magnitude = math.sqrt(
            dimensions.valence**2 + dimensions.arousal**2 + dimensions.dominance**2
        )
        confidence += magnitude * 0.2

        # 基于文本长度调整置信度
        if len(text) > 10:
            confidence += 0.1

        return min(1.0, confidence)

    def _update_emotion_history(self, user_id: int, emotion_state: EmotionState):
        """更新用户情感历史"""
        if user_id not in self.emotion_history:
            self.emotion_history[user_id] = []

        self.emotion_history[user_id].append(emotion_state)

        # 只保留最近20条记录
        if len(self.emotion_history[user_id]) > 20:
            self.emotion_history[user_id] = self.emotion_history[user_id][-20:]

    def get_emotion_trajectory(self, user_id: int) -> List[EmotionState]:
        """获取用户情感轨迹"""
        return self.emotion_history.get(user_id, [])

    def _call_api(
        self, prompt: str, system_prompt: Optional[str] = None
    ) -> Optional[str]:
        """调用AI API"""
        if not self.api_key:
            return None

        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }

            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            payload = {
                "model": DEFAULT_MODEL,
                "messages": messages,
                "max_tokens": 200,
                "temperature": 0.1,
            }

            response = requests.post(
                ZHIPUAI_API_ENDPOINT, headers=headers, json=payload, timeout=5
            )
            response.raise_for_status()
            response_json = response.json()

            if (
                response_json
                and "choices" in response_json
                and response_json["choices"]
            ):
                return (
                    response_json["choices"][0]
                    .get("message", {})
                    .get("content", "")
                    .strip()
                )

        except Exception as e:
            logger.error(f"API调用失败: {e}")

        return None

    def get_optimal_animation_with_transition(
        self, emotion_state: EmotionState, user_id: Optional[int] = None
    ) -> Tuple[str, bool]:
        """
        获取最优动画状态，考虑过渡平滑性

        Args:
            emotion_state: 情感状态
            user_id: 用户ID，用于动画历史追踪

        Returns:
            Tuple[str, bool]: (动画状态, 是否需要过渡动画)
        """
        target_animation = emotion_state.to_animation_state()

        # 如果是特殊动画状态，直接返回，不进行过渡处理
        if (
            hasattr(emotion_state, "_special_animation")
            and emotion_state._special_animation
        ):
            if user_id:
                self.current_animation[user_id] = target_animation
                self._update_animation_history(user_id, target_animation)
            logger.info(f"使用特殊动画状态: {target_animation}")
            return target_animation, False

        if not user_id:
            return target_animation, False

        current_animation = self.current_animation.get(user_id, "idle")

        # 如果目标动画与当前动画相同，无需切换
        if target_animation == current_animation:
            return target_animation, False

        # 检查是否可以直接过渡
        can_direct_transition = self._can_direct_transition(
            current_animation, target_animation
        )

        if can_direct_transition:
            # 更新当前动画状态
            self.current_animation[user_id] = target_animation
            self._update_animation_history(user_id, target_animation)
            return target_animation, False
        else:
            # 需要通过中间动画过渡
            transition_animation = self._find_transition_animation(
                current_animation, target_animation
            )

            if transition_animation:
                # 先切换到过渡动画
                self.current_animation[user_id] = transition_animation
                self._update_animation_history(user_id, transition_animation)
                logger.info(
                    f"用户 {user_id} 动画过渡: {current_animation} -> {transition_animation} -> {target_animation}"
                )
                return transition_animation, True
            else:
                # 无法找到合适过渡，直接切换
                self.current_animation[user_id] = target_animation
                self._update_animation_history(user_id, target_animation)
                logger.warning(
                    f"用户 {user_id} 强制动画切换: {current_animation} -> {target_animation}"
                )
                return target_animation, False

    def _can_direct_transition(self, from_animation: str, to_animation: str) -> bool:
        """检查两个动画是否可以直接过渡"""
        if from_animation not in ANIMATION_TRANSITIONS:
            return True  # 未知动画，允许直接切换

        return to_animation in ANIMATION_TRANSITIONS[from_animation]

    def _find_transition_animation(
        self, from_animation: str, to_animation: str
    ) -> Optional[str]:
        """寻找两个动画之间的过渡动画"""
        if from_animation not in ANIMATION_TRANSITIONS:
            return None

        # 寻找共同的中间动画
        from_transitions = set(ANIMATION_TRANSITIONS[from_animation])

        if to_animation not in ANIMATION_TRANSITIONS:
            # 目标动画未定义过渡规则，使用idle作为中间过渡
            if "idle" in from_transitions:
                return "idle"
            return None

        to_transitions = set(ANIMATION_TRANSITIONS.get(to_animation, []))

        # 寻找共同的过渡动画
        common_transitions = from_transitions.intersection(to_transitions)

        if common_transitions:
            # 优先选择idle或confused作为过渡
            if "idle" in common_transitions:
                return "idle"
            elif "confused" in common_transitions:
                return "confused"
            else:
                return list(common_transitions)[0]

        # 如果没有共同过渡，尝试通过idle中转
        if "idle" in from_transitions and to_animation in ANIMATION_TRANSITIONS.get(
            "idle", []
        ):
            return "idle"

        return None

    def _update_animation_history(self, user_id: int, animation: str):
        """更新用户动画历史"""
        if user_id not in self.animation_history:
            self.animation_history[user_id] = []

        self.animation_history[user_id].append(animation)

        # 只保留最近10条动画记录
        if len(self.animation_history[user_id]) > 10:
            self.animation_history[user_id] = self.animation_history[user_id][-10:]

    def _apply_emotional_context(
        self, emotion_state: EmotionState, user_id: Optional[int]
    ) -> EmotionState:
        """
        应用情感上下文，基于用户的情感历史调整当前情感分析

        Args:
            emotion_state: 当前分析的情感状态
            user_id: 用户ID

        Returns:
            调整后的情感状态
        """
        # 如果是特殊动画状态，不进行上下文调整
        if (
            hasattr(emotion_state, "_special_animation")
            and emotion_state._special_animation
        ):
            return emotion_state

        if not user_id or user_id not in self.emotion_history:
            return emotion_state

        history = self.emotion_history[user_id]
        if len(history) < 2:
            return emotion_state

        # 获取最近的情感状态
        recent_emotions = history[-3:]  # 最近3次情感

        # 计算情感趋势
        valence_trend = self._calculate_emotion_trend(recent_emotions, "valence")
        arousal_trend = self._calculate_emotion_trend(recent_emotions, "arousal")

        # 基于趋势微调当前情感
        adjusted_dimensions = EmotionDimensions(
            valence=max(
                -1.0, min(1.0, emotion_state.dimensions.valence + valence_trend * 0.1)
            ),
            arousal=max(
                -1.0, min(1.0, emotion_state.dimensions.arousal + arousal_trend * 0.1)
            ),
            dominance=emotion_state.dimensions.dominance,
        )

        # 检查情感波动
        if self._is_emotional_volatility_high(recent_emotions):
            # 如果情感波动大，降低置信度
            adjusted_confidence = max(0.1, emotion_state.confidence - 0.2)
        else:
            adjusted_confidence = emotion_state.confidence

        return EmotionState(
            primary_emotion=emotion_state.primary_emotion,
            intensity=emotion_state.intensity,
            dimensions=adjusted_dimensions,
            secondary_emotions=emotion_state.secondary_emotions,
            confidence=adjusted_confidence,
        )

    def _calculate_emotion_trend(
        self, recent_emotions: List[EmotionState], dimension: str
    ) -> float:
        """计算情感维度的趋势"""
        if len(recent_emotions) < 2:
            return 0.0

        values = []
        for emotion in recent_emotions:
            if dimension == "valence":
                values.append(emotion.dimensions.valence)
            elif dimension == "arousal":
                values.append(emotion.dimensions.arousal)
            elif dimension == "dominance":
                values.append(emotion.dimensions.dominance)

        if len(values) < 2:
            return 0.0

        # 计算简单的线性趋势
        trend = (values[-1] - values[0]) / len(values)
        return trend

    def _is_emotional_volatility_high(
        self, recent_emotions: List[EmotionState]
    ) -> bool:
        """检查情感波动是否剧烈"""
        if len(recent_emotions) < 3:
            return False

        # 计算情感变化的标准差
        valences = [e.dimensions.valence for e in recent_emotions]
        arousals = [e.dimensions.arousal for e in recent_emotions]

        import statistics

        try:
            valence_std = statistics.stdev(valences) if len(valences) > 1 else 0
            arousal_std = statistics.stdev(arousals) if len(arousals) > 1 else 0

            # 如果标准差较大，认为情感波动剧烈
            return valence_std > 0.5 or arousal_std > 0.5
        except:
            return False

    def _detect_special_text_types(self, text: str) -> Optional[str]:
        """
        检测特殊文本类型，返回对应的动画状态

        Args:
            text: 待分析文本

        Returns:
            Optional[str]: 如果是特殊类型，返回对应动画；否则返回None
        """
        text_lower = text.lower().strip()

        # 互动性问句 - thinking
        interactive_patterns = [
            "你猜",
            "猜猜",
            "你觉得",
            "你认为",
            "你说",
            "你想",
            "你看",
            "怎么样",
            "如何",
            "什么样",
            "好不好",
            "对不对",
            "是不是",
        ]

        # 询问类问句 - thinking
        inquiry_patterns = [
            "怎么办",
            "怎么做",
            "如何",
            "什么意思",
            "为什么",
            "哪里",
            "什么时候",
            "有什么",
            "能不能",
            "可以吗",
            "行吗",
            "好吗",
        ]

        # 打招呼/日常对话 - happy
        greeting_patterns = [
            "你好",
            "hi",
            "hello",
            "早上好",
            "晚上好",
            "最近怎么样",
            "在干嘛",
            "在做什么",
            "聊天",
            "说话",
        ]

        # 测试/试探 - confused
        test_patterns = ["测试", "试试", "看看", "检查", "test", "试探"]

        # 检查是否包含问号
        has_question_mark = "?" in text or "？" in text

        # 检查各种模式
        for pattern in interactive_patterns:
            if pattern in text_lower:
                return "thinking"  # 互动性问句用thinking

        for pattern in inquiry_patterns:
            if pattern in text_lower:
                return "thinking"  # 询问类问句用thinking

        for pattern in greeting_patterns:
            if pattern in text_lower:
                return "happy"  # 打招呼用happy

        for pattern in test_patterns:
            if pattern in text_lower:
                return "confused"  # 测试用confused

        # 如果有问号但没有匹配到特定模式，使用thinking
        if has_question_mark and len(text.strip()) < 20:  # 短问句
            return "thinking"

        return None  # 不是特殊类型，使用正常的情感分析

    def generate_smart_status_text(
        self,
        emotion_state: EmotionState,
        animation_state: str,
        user_id: Optional[int] = None,
        user_input: Optional[str] = None,
    ) -> str:
        """
        生成智能的状态文字提示，配合动画状态和情感分析结果

        Args:
            emotion_state: 情感状态
            animation_state: 动画状态
            user_id: 用户ID，用于个性化提示
            user_input: 用户输入，用于生成更贴切的回应

        Returns:
            str: 合适的状态文字提示
        """
        import random

        try:
            # 使用全局常量 - 确保正确引用
            global ANIMATION_TEXT_PROMPTS, INTENSITY_TEXT_MODIFIERS, CONTEXTUAL_TEXT_PROMPTS

            # 1. 获取基础文字提示
            base_prompts = ANIMATION_TEXT_PROMPTS.get(
                animation_state, ["我在这里陪着你~"]
            )

            # 2. 根据情感强度调整文字
            intensity_prompts = INTENSITY_TEXT_MODIFIERS.get(
                emotion_state.intensity, {}
            ).get(animation_state, [])

            # 3. 获取上下文相关的个性化提示
            contextual_prompts = self._get_contextual_prompts(user_id, emotion_state)

            # 4. 合并所有可能的提示
            all_prompts = base_prompts.copy()

            # 如果有强度相关的提示，优先使用
            if intensity_prompts:
                all_prompts.extend(intensity_prompts)

            # 如果有上下文相关的提示，也加入候选
            if contextual_prompts:
                all_prompts.extend(contextual_prompts)

            # 5. 根据置信度决定是否使用更具体的提示
            if emotion_state.confidence > 0.7:
                # 高置信度时，可以使用更具体的情感表达
                specific_prompts = self._get_emotion_specific_prompts(
                    emotion_state, user_input
                )
                if specific_prompts:
                    all_prompts.extend(specific_prompts)

            # 6. 随机选择一个提示
            selected_prompt = random.choice(all_prompts)

            # 7. 根据次要情感进行微调
            if emotion_state.secondary_emotions:
                selected_prompt = self._adjust_prompt_for_secondary_emotions(
                    selected_prompt, emotion_state.secondary_emotions
                )

            logger.debug(
                f"Generated status text: '{selected_prompt}' for animation: {animation_state}"
            )
            return selected_prompt

        except Exception as e:
            logger.error(f"Error generating smart status text: {e}")
            # 安全回退 - 使用全局常量
            try:
                return ANIMATION_TEXT_PROMPTS.get(animation_state, ["我在这里陪着你~"])[
                    0
                ]
            except:
                return "我在这里陪着你~"

    def _get_contextual_prompts(
        self, user_id: Optional[int], emotion_state: EmotionState
    ) -> List[str]:
        """获取基于用户历史的上下文相关提示"""
        global CONTEXTUAL_TEXT_PROMPTS

        if not user_id or user_id not in self.emotion_history:
            return CONTEXTUAL_TEXT_PROMPTS.get("first_interaction", [])

        history = self.emotion_history[user_id]
        if len(history) < 2:
            return CONTEXTUAL_TEXT_PROMPTS.get("first_interaction", [])

        # 分析用户的情感模式
        recent_emotions = history[-5:]  # 最近5次情感
        positive_count = sum(1 for e in recent_emotions if e.dimensions.valence > 0.2)
        negative_count = sum(1 for e in recent_emotions if e.dimensions.valence < -0.2)

        # 检查情感改善
        if len(history) >= 3:
            prev_valence = history[-3].dimensions.valence
            curr_valence = emotion_state.dimensions.valence
            if prev_valence < -0.3 and curr_valence > 0.1:
                return CONTEXTUAL_TEXT_PROMPTS.get("mood_improvement", [])

        # 检查情感波动
        if self._is_emotional_volatility_high(recent_emotions):
            return CONTEXTUAL_TEXT_PROMPTS.get("emotional_volatility", [])

        # 基于整体情感倾向
        if positive_count > negative_count * 2:
            return CONTEXTUAL_TEXT_PROMPTS.get("frequent_positive", [])
        elif negative_count > positive_count:
            return CONTEXTUAL_TEXT_PROMPTS.get("frequent_negative", [])

        return []

    def _get_emotion_specific_prompts(
        self, emotion_state: EmotionState, user_input: Optional[str]
    ) -> List[str]:
        """根据特定情感和用户输入生成更贴切的提示"""
        if not user_input:
            return []

        user_input_lower = user_input.lower()
        primary_emotion = emotion_state.primary_emotion
        intensity = emotion_state.intensity

        # 根据用户输入和情感生成特定回应
        specific_prompts = []

        # Joy/happiness 相关
        if primary_emotion == PlutchikEmotions.JOY:
            if any(
                word in user_input_lower
                for word in ["成功", "通过", "考试", "工作", "升职"]
            ):
                if intensity == EmotionIntensity.HIGH:
                    specific_prompts.extend(
                        [
                            "哇！这个好消息让我都兴奋起来了！",
                            "太棒了！我为你的成功感到骄傲！",
                        ]
                    )
                else:
                    specific_prompts.extend(["真为你高兴！", "这是个好消息呢~"])
            elif any(word in user_input_lower for word in ["开心", "快乐", "高兴"]):
                specific_prompts.extend(
                    ["你的快乐也感染了我！", "看到你开心，我也很开心~"]
                )

        # Fear/anxiety 相关
        elif primary_emotion == PlutchikEmotions.FEAR:
            if any(
                word in user_input_lower for word in ["考试", "面试", "工作", "明天"]
            ):
                specific_prompts.extend(
                    ["我理解你的紧张，我会陪着你的", "深呼吸，我相信你可以的"]
                )
            elif any(word in user_input_lower for word in ["担心", "害怕", "紧张"]):
                specific_prompts.extend(
                    ["我能感受到你的不安...", "让我陪你一起面对这些担忧"]
                )

        # Sadness 相关
        elif primary_emotion == PlutchikEmotions.SADNESS:
            if any(word in user_input_lower for word in ["失败", "没通过", "不行"]):
                specific_prompts.extend(
                    ["虽然这次没有成功，但我相信你！", "挫折是成长的一部分，我陪着你"]
                )
            elif any(word in user_input_lower for word in ["难过", "伤心", "失望"]):
                specific_prompts.extend(
                    ["我能理解你现在的感受...", "难过的时候，我在这里陪你"]
                )

        # Surprise 相关
        elif primary_emotion == PlutchikEmotions.SURPRISE:
            if "没想到" in user_input_lower or "惊讶" in user_input_lower:
                specific_prompts.extend(
                    ["这确实很出人意料呢！", "我也被你说的话惊到了！"]
                )

        return specific_prompts

    def _adjust_prompt_for_secondary_emotions(
        self, prompt: str, secondary_emotions: List[Tuple[PlutchikEmotions, float]]
    ) -> str:
        """根据次要情感微调提示语"""
        if not secondary_emotions:
            return prompt

        # 如果有强烈的次要情感，可能需要在提示中体现
        for emotion, weight in secondary_emotions:
            if weight > 0.6:  # 权重较高的次要情感
                if emotion == PlutchikEmotions.FEAR and "开心" in prompt:
                    # 如果主要情感是开心但有恐惧的次要情感
                    return prompt + "不过你好像还有一些担心？"
                elif emotion == PlutchikEmotions.SADNESS and "兴奋" in prompt:
                    # 如果主要情感是兴奋但有悲伤的次要情感
                    return prompt + "但是我感觉你心情有些复杂..."
                elif emotion == PlutchikEmotions.JOY and "担心" in prompt:
                    # 如果主要情感是担心但有快乐的次要情感
                    return prompt + "不过我也感受到了一些积极的情绪~"

        return prompt


# 全局情感分析器实例
emotion_analyzer = EmotionAnalyzer()


# 兼容性函数（为了保持与现有代码的兼容性）
def analyze_emotion_for_pet(
    user_id: int,
    reflection_text: str,
    status_callback: Optional[Callable[[str], None]] = None,
) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    为宠物系统提供情感分析（兼容性包装器）

    Returns:
        Tuple[Optional[str], Optional[str], Optional[str]]: (情感名称, 动画状态, 状态文字)
    """
    if not reflection_text:
        logger.warning(f"Cannot analyze empty reflection text for user {user_id}.")
        if status_callback:
            status_callback(ANIMATION_STATES["idle"])
        return None, ANIMATION_STATES["idle"], "我在这里陪着你呢~"

    # 立即切换到thinking动画
    if status_callback:
        status_callback(ANIMATION_STATES["thinking"])

    try:
        # 使用新的高级情感分析
        emotion_state = emotion_analyzer.analyze_emotion_advanced(
            text=reflection_text, user_id=user_id
        )

        # 使用智能动画过渡系统
        optimal_animation, needs_transition = (
            emotion_analyzer.get_optimal_animation_with_transition(
                emotion_state, user_id
            )
        )

        # 生成智能状态文字
        smart_status_text = emotion_analyzer.generate_smart_status_text(
            emotion_state=emotion_state,
            animation_state=optimal_animation,
            user_id=user_id,
            user_input=reflection_text,
        )

        # 转换为旧格式
        emotion_name = emotion_state.primary_emotion.value

        logger.info(
            f"情感分析结果: {emotion_name} -> {optimal_animation} "
            f"(强度: {emotion_state.intensity.value}, "
            f"置信度: {emotion_state.confidence:.2f}, "
            f"需要过渡: {needs_transition})"
        )
        logger.info(f"智能状态文字: {smart_status_text}")

        if status_callback:
            status_callback(optimal_animation)

        return emotion_name, optimal_animation, smart_status_text

    except Exception as e:
        logger.error(f"情感分析失败: {e}")
        if status_callback:
            status_callback(ANIMATION_STATES["concerned"])
        return None, ANIMATION_STATES["concerned"], "我有点担心你呢..."


def test_emotion_analysis():
    """测试情感分析和动画系统"""

    test_cases = [
        ("我今天真的很开心，一切都很顺利！", "应该表现为高兴/兴奋"),
        ("我有点担心明天的考试...", "应该表现为担忧"),
        ("哇，这真是太令人惊讶了！", "应该表现为惊讶/困惑"),
        ("我感觉有点难过和失落", "应该表现为担忧"),
        ("我对这个项目很有信心", "应该表现为积极/开心"),
        ("我很期待即将到来的假期", "应该表现为期待/兴奋"),
        ("我考试考了满分！", "应该表现为兴奋/开心"),
        ("我成功了！太棒了！", "应该表现为兴奋/开心"),
        # 新增特殊文本类型测试
        ("你猜我今天心情怎么样", "应该表现为思考"),
        ("你觉得我应该怎么办？", "应该表现为思考"),
        ("你好！", "应该表现为开心"),
        ("测试一下", "应该表现为困惑"),
        ("什么意思？", "应该表现为思考"),
    ]

    analyzer = EmotionAnalyzer()

    print("=" * 60)
    print("测试智能状态文字功能")
    print("=" * 60)

    for i, (text, expected) in enumerate(test_cases, 1):
        print(f"\n测试 {i}: {text}")
        print(f"预期: {expected}")

        try:
            # 分析情感
            emotion_state = analyzer.analyze_emotion_advanced(text, user_id=1)

            # 获取动画
            animation, needs_transition = (
                analyzer.get_optimal_animation_with_transition(emotion_state, user_id=1)
            )

            # 生成智能状态文字
            smart_text = analyzer.generate_smart_status_text(
                emotion_state=emotion_state,
                animation_state=animation,
                user_id=1,
                user_input=text,
            )

            print(f"结果:")
            print(f"  主要情感: {emotion_state.primary_emotion.value}")
            print(f"  强度: {emotion_state.intensity.value}")
            print(f"  置信度: {emotion_state.confidence:.2f}")
            print(
                f"  维度: V={emotion_state.dimensions.valence:.2f}, "
                f"A={emotion_state.dimensions.arousal:.2f}, "
                f"D={emotion_state.dimensions.dominance:.2f}"
            )
            print(f"  次要情感: {emotion_state.secondary_emotions}")
            print(f"  动画状态: {animation}")
            print(f"  需要过渡: {needs_transition}")
            print(f"  智能状态文字: '{smart_text}'")

            # 如果是特殊类型，显示特殊标记
            if (
                hasattr(emotion_state, "_special_animation")
                and emotion_state._special_animation
            ):
                print(f"  [特殊类型]: {emotion_state._special_animation}")

        except Exception as e:
            print(f"错误: {e}")

    # 测试兼容性函数
    print(f"\n" + "=" * 60)
    print("测试兼容性函数 analyze_emotion_for_pet")
    print("=" * 60)

    test_text = "我今天考试考了满分！太开心了！"
    try:
        emotion_name, animation_state, status_text = analyze_emotion_for_pet(
            user_id=1, reflection_text=test_text
        )
        print(f"输入: {test_text}")
        print(f"情感名称: {emotion_name}")
        print(f"动画状态: {animation_state}")
        print(f"状态文字: {status_text}")
    except Exception as e:
        print(f"兼容性函数测试错误: {e}")

    # 测试动画过渡
    print(f"\n动画过渡测试:")
    print(f"当前动画历史: {analyzer.animation_history.get(1, [])}")
    print(f"当前动画状态: {analyzer.current_animation.get(1, 'idle')}")
    print("=" * 60)


if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.DEBUG)

    # Run tests
    print("Starting emotion analysis tests...")
    test_emotion_analysis()
    print("\nTests completed.")
