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

    def to_animation_state(self) -> str:
        """转换为动画状态"""
        return EMOTION_TO_ANIMATION.get(self.primary_emotion.value, "idle")


# 情感到动画的映射（基于Plutchik理论）
EMOTION_TO_ANIMATION = {
    PlutchikEmotions.JOY.value: "happy",
    PlutchikEmotions.TRUST.value: "happy",
    PlutchikEmotions.FEAR.value: "concerned",
    PlutchikEmotions.SURPRISE.value: "confused",
    PlutchikEmotions.SADNESS.value: "concerned",
    PlutchikEmotions.DISGUST.value: "concerned",
    PlutchikEmotions.ANGER.value: "concerned",
    PlutchikEmotions.ANTICIPATION.value: "excited",
}

# Animation states
ANIMATION_STATES = {
    "thinking": "thinking",
    "idle": "idle",
    "happy": "happy",
    "concerned": "concerned",
    "confused": "confused",
    "excited": "excited",
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
    PlutchikEmotions.SURPRISE: ["惊讶", "意外", "震惊", "诧异", "吃惊", "惊奇"],
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
    ],
}


class EmotionAnalyzer:
    """基于科学理论的情感分析器"""

    def __init__(self):
        self.api_key = self._get_api_key()
        self.emotion_history: Dict[int, List[EmotionState]] = {}  # 用户情感历史

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

            # 6. 更新用户情感历史
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

        # 愉悦度关键词
        positive_words = ["开心", "快乐", "高兴", "愉快", "喜悦", "满意", "棒", "好"]
        negative_words = ["难过", "伤心", "痛苦", "失望", "沮丧", "糟糕", "差", "不好"]

        # 唤醒度关键词
        high_arousal_words = ["兴奋", "激动", "紧张", "焦虑", "愤怒", "害怕", "震惊"]
        low_arousal_words = ["平静", "放松", "疲惫", "困倦", "安静", "淡定"]

        # 控制度关键词
        high_dominance_words = ["控制", "决定", "主动", "自信", "强大", "能够", "可以"]
        low_dominance_words = ["无助", "被动", "依赖", "脆弱", "不能", "没办法", "无奈"]

        # 计算维度得分
        for word in positive_words:
            if word in text_lower:
                valence_score += 0.3
        for word in negative_words:
            if word in text_lower:
                valence_score -= 0.3

        for word in high_arousal_words:
            if word in text_lower:
                arousal_score += 0.3
        for word in low_arousal_words:
            if word in text_lower:
                arousal_score -= 0.3

        for word in high_dominance_words:
            if word in text_lower:
                dominance_score += 0.3
        for word in low_dominance_words:
            if word in text_lower:
                dominance_score -= 0.3

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
            intensity = self._calculate_intensity_from_dimensions(dimensions)
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
        intensity = self._calculate_intensity_from_dimensions(dimensions)

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


# 全局情感分析器实例
emotion_analyzer = EmotionAnalyzer()


# 兼容性函数（为了保持与现有代码的兼容性）
def analyze_emotion_for_pet(
    user_id: int,
    reflection_text: str,
    status_callback: Optional[Callable[[str], None]] = None,
) -> Tuple[Optional[str], Optional[str]]:
    """
    为宠物系统提供情感分析（兼容性包装器）
    """
    if not reflection_text:
        logger.warning(f"Cannot analyze empty reflection text for user {user_id}.")
        if status_callback:
            status_callback(ANIMATION_STATES["idle"])
        return None, ANIMATION_STATES["idle"]

    # 立即切换到thinking动画
    if status_callback:
        status_callback(ANIMATION_STATES["thinking"])

    try:
        # 使用新的高级情感分析
        emotion_state = emotion_analyzer.analyze_emotion_advanced(
            text=reflection_text, user_id=user_id
        )

        # 转换为旧格式
        emotion_name = emotion_state.primary_emotion.value
        animation_state = emotion_state.to_animation_state()

        logger.info(f"情感分析结果: {emotion_name} -> {animation_state}")

        if status_callback:
            status_callback(animation_state)

        return emotion_name, animation_state

    except Exception as e:
        logger.error(f"情感分析失败: {e}")
        if status_callback:
            status_callback(ANIMATION_STATES["concerned"])
        return None, ANIMATION_STATES["concerned"]


if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.DEBUG)

    # Run tests
    print("Starting emotion analysis tests...")
    test_emotion_analysis()
    print("\nTests completed.")
