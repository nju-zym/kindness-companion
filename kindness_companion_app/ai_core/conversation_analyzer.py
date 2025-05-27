"""
基于CBT认知行为疗法理论的对话分析模块

本模块实现以下功能：
1. 基于Aaron Beck认知疗法的认知扭曲识别
2. Albert Ellis理性情绪疗法的非理性信念检测
3. 苏格拉底式询问法的对话引导
4. 认知重构和行为激活建议
5. 用户心理画像分析和存储
"""

import logging
import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from enum import Enum
from dataclasses import dataclass

from .api_client import get_api_key, make_api_request

logger = logging.getLogger(__name__)

# API configuration
ZHIPUAI_API_ENDPOINT = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
DEFAULT_MODEL = "glm-4"


# 基于Beck的认知扭曲类型
class CognitiveDistortion(Enum):
    """Beck认知疗法中的十大认知扭曲"""

    ALL_OR_NOTHING = "all_or_nothing"  # 全有全无思维
    OVERGENERALIZATION = "overgeneralization"  # 过度泛化
    MENTAL_FILTER = "mental_filter"  # 心理过滤
    DISQUALIFYING_POSITIVE = "disqualifying_positive"  # 否定积极面
    JUMPING_TO_CONCLUSIONS = "jumping_to_conclusions"  # 妄下结论
    MAGNIFICATION = "magnification"  # 夸大
    EMOTIONAL_REASONING = "emotional_reasoning"  # 情绪化推理
    SHOULD_STATEMENTS = "should_statements"  # 应该句式
    LABELING = "labeling"  # 贴标签
    PERSONALIZATION = "personalization"  # 个人化


# Ellis理性情绪疗法的非理性信念类型
class IrrationalBelief(Enum):
    """Ellis RET理论的非理性信念"""

    DEMAND_FOR_APPROVAL = "demand_for_approval"  # 需要获得所有人的认可
    HIGH_SELF_EXPECTATIONS = "high_self_expectations"  # 对自己有过高期望
    BLAME_PRONENESS = "blame_proneness"  # 责备倾向
    FRUSTRATION_INTOLERANCE = "frustration_intolerance"  # 挫折不耐受
    EMOTIONAL_IRRESPONSIBILITY = "emotional_irresponsibility"  # 情绪不负责任
    ANXIOUS_OVERCONCERN = "anxious_overconcern"  # 过度担忧
    PROBLEM_AVOIDANCE = "problem_avoidance"  # 问题回避
    DEPENDENCY = "dependency"  # 依赖性
    HELPLESSNESS = "helplessness"  # 无助感
    PERFECTIONISM = "perfectionism"  # 完美主义


# 苏格拉底式询问类型
class SocraticQuestionType(Enum):
    """苏格拉底式询问的问题类型"""

    CLARIFICATION = "clarification"  # 澄清问题
    ASSUMPTION = "assumption"  # 假设问题
    EVIDENCE = "evidence"  # 证据问题
    PERSPECTIVE = "perspective"  # 视角问题
    IMPLICATION = "implication"  # 含义问题
    META_QUESTION = "meta_question"  # 元问题


@dataclass
class CognitiveAnalysisResult:
    """认知分析结果"""

    distortions: List[Tuple[CognitiveDistortion, float]]  # 认知扭曲及其严重程度
    irrational_beliefs: List[Tuple[IrrationalBelief, float]]  # 非理性信念及其强度
    core_beliefs: List[str]  # 核心信念
    automatic_thoughts: List[str]  # 自动化思维
    emotional_patterns: Dict[str, float]  # 情绪模式
    behavioral_patterns: List[str]  # 行为模式
    confidence: float  # 分析置信度


@dataclass
class SocraticResponse:
    """苏格拉底式响应"""

    question_type: SocraticQuestionType
    question: str
    purpose: str  # 问题目的
    follow_up_suggestions: List[str]  # 后续建议


# 认知扭曲的中文关键词映射
COGNITIVE_DISTORTION_KEYWORDS = {
    CognitiveDistortion.ALL_OR_NOTHING: [
        "总是",
        "从来",
        "永远",
        "绝对",
        "完全",
        "一定",
        "肯定",
        "必须",
        "完全不",
        "根本不",
    ],
    CognitiveDistortion.OVERGENERALIZATION: [
        "所有人",
        "每个人",
        "都是",
        "总是这样",
        "永远这样",
        "一直",
        "从来都",
    ],
    CognitiveDistortion.MENTAL_FILTER: [
        "只是",
        "仅仅",
        "就是",
        "不过是",
        "只不过",
        "除了",
        "但是",
        "然而",
    ],
    CognitiveDistortion.DISQUALIFYING_POSITIVE: [
        "不算什么",
        "只是运气",
        "碰巧",
        "侥幸",
        "偶然",
        "意外",
        "不值得",
    ],
    CognitiveDistortion.JUMPING_TO_CONCLUSIONS: [
        "肯定是",
        "一定是",
        "显然",
        "明显",
        "当然",
        "毫无疑问",
        "绝对是",
    ],
    CognitiveDistortion.MAGNIFICATION: [
        "灾难性",
        "糟透了",
        "完蛋了",
        "毁了",
        "可怕",
        "恐怖",
        "最坏",
    ],
    CognitiveDistortion.EMOTIONAL_REASONING: [
        "感觉",
        "觉得",
        "认为",
        "我想",
        "好像",
        "似乎",
        "可能",
    ],
    CognitiveDistortion.SHOULD_STATEMENTS: [
        "应该",
        "必须",
        "应当",
        "理应",
        "本应",
        "不应该",
        "不能",
        "必须要",
    ],
    CognitiveDistortion.LABELING: [
        "我是",
        "他是",
        "就是",
        "本来就",
        "天生",
        "性格",
        "命",
    ],
    CognitiveDistortion.PERSONALIZATION: [
        "我的错",
        "因为我",
        "如果我",
        "要是我",
        "都是我",
        "怪我",
    ],
}

# 非理性信念的关键词映射
IRRATIONAL_BELIEF_KEYWORDS = {
    IrrationalBelief.DEMAND_FOR_APPROVAL: [
        "别人怎么看",
        "大家认为",
        "被喜欢",
        "被接受",
        "被认可",
        "讨厌我",
    ],
    IrrationalBelief.HIGH_SELF_EXPECTATIONS: [
        "完美",
        "最好",
        "优秀",
        "成功",
        "失败",
        "不够好",
        "做不到",
    ],
    IrrationalBelief.FRUSTRATION_INTOLERANCE: [
        "受不了",
        "无法忍受",
        "太难了",
        "不公平",
        "为什么",
        "凭什么",
    ],
    IrrationalBelief.PERFECTIONISM: [
        "完美",
        "完全正确",
        "不能出错",
        "必须做好",
        "一点不能错",
    ],
}

# 苏格拉底式问题模板
SOCRATIC_QUESTION_TEMPLATES = {
    SocraticQuestionType.CLARIFICATION: [
        "你能更具体地解释一下这个想法吗？",
        "当你说'{key_phrase}'时，你具体指的是什么？",
        "能举个具体的例子来说明吗？",
    ],
    SocraticQuestionType.ASSUMPTION: [
        "这个想法基于什么假设？",
        "你是如何得出这个结论的？",
        "还有其他可能的解释吗？",
    ],
    SocraticQuestionType.EVIDENCE: [
        "有什么证据支持这个想法？",
        "有什么证据与这个想法相矛盾？",
        "如果要反驳这个想法，你会怎么说？",
    ],
    SocraticQuestionType.PERSPECTIVE: [
        "如果是你的好朋友遇到同样的情况，你会怎么对他们说？",
        "从另一个角度来看，这件事可能意味着什么？",
        "五年后回看这件事，你觉得它还会这么重要吗？",
    ],
    SocraticQuestionType.IMPLICATION: [
        "如果这个想法是真的，那意味着什么？",
        "这种思维方式对你的感受有什么影响？",
        "继续这样想下去会发生什么？",
    ],
}


class CBTConversationAnalyzer:
    """基于CBT理论的对话分析器"""

    def __init__(self, db_manager):
        """
        初始化CBT对话分析器

        Args:
            db_manager: 数据库管理器实例
        """
        self.db_manager = db_manager
        self._ensure_tables_exist()
        self.api_key = get_api_key("ZHIPUAI")
        self.max_context_length = 50
        self.max_history_age_days = 30

    def _ensure_tables_exist(self):
        """确保必要的数据库表存在"""
        self.db_manager.connect()

        # 原有表结构保持不变，添加CBT相关表

        # 对话历史表
        self.db_manager.cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS conversation_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            message TEXT NOT NULL,
            is_user INTEGER NOT NULL DEFAULT 1,  -- 1 for user, 0 for AI
            context_id TEXT,
            topic TEXT DEFAULT 'general',
            emotion_score FLOAT DEFAULT 0.0,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        """
        )

        # 认知分析结果表
        self.db_manager.cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS cognitive_analysis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            message_text TEXT NOT NULL,
            distortions TEXT,  -- JSON string of cognitive distortions
            irrational_beliefs TEXT,  -- JSON string of irrational beliefs
            core_beliefs TEXT,  -- JSON string of core beliefs
            automatic_thoughts TEXT,  -- JSON string of automatic thoughts
            analysis_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            confidence_score FLOAT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        """
        )

        # 苏格拉底式对话记录表
        self.db_manager.cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS socratic_dialogue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            question_type TEXT NOT NULL,
            question_text TEXT NOT NULL,
            user_response TEXT,
            effectiveness_score FLOAT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        """
        )

        # 认知重构进展表
        self.db_manager.cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS cognitive_restructuring (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            original_thought TEXT NOT NULL,
            restructured_thought TEXT NOT NULL,
            technique_used TEXT,  -- 使用的技术
            effectiveness_rating INTEGER,  -- 1-5评分
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        """
        )

        self.db_manager.connection.commit()
        self.db_manager.disconnect()

    def analyze_cognitive_patterns(
        self, user_id: int, message: str, context: Optional[List[str]] = None
    ) -> CognitiveAnalysisResult:
        """
        基于CBT理论分析用户的认知模式

        Args:
            user_id: 用户ID
            message: 用户消息
            context: 对话上下文

        Returns:
            CognitiveAnalysisResult: 认知分析结果
        """
        try:
            # 1. 识别认知扭曲
            distortions = self._identify_cognitive_distortions(message)

            # 2. 识别非理性信念
            irrational_beliefs = self._identify_irrational_beliefs(message)

            # 3. 提取核心信念和自动化思维
            core_beliefs, automatic_thoughts = self._extract_beliefs_and_thoughts(
                message, context
            )

            # 4. 分析情绪模式
            emotional_patterns = self._analyze_emotional_patterns(message)

            # 5. 识别行为模式
            behavioral_patterns = self._identify_behavioral_patterns(message)

            # 6. 计算分析置信度
            confidence = self._calculate_analysis_confidence(
                message, distortions, irrational_beliefs, core_beliefs
            )

            result = CognitiveAnalysisResult(
                distortions=distortions,
                irrational_beliefs=irrational_beliefs,
                core_beliefs=core_beliefs,
                automatic_thoughts=automatic_thoughts,
                emotional_patterns=emotional_patterns,
                behavioral_patterns=behavioral_patterns,
                confidence=confidence,
            )

            # 存储分析结果
            self._store_cognitive_analysis(user_id, message, result)

            logger.info(f"用户{user_id}的认知分析完成，置信度: {confidence:.2f}")
            return result

        except Exception as e:
            logger.error(f"认知模式分析失败: {e}")
            return CognitiveAnalysisResult(
                distortions=[],
                irrational_beliefs=[],
                core_beliefs=[],
                automatic_thoughts=[],
                emotional_patterns={},
                behavioral_patterns=[],
                confidence=0.1,
            )

    def _identify_cognitive_distortions(
        self, message: str
    ) -> List[Tuple[CognitiveDistortion, float]]:
        """识别认知扭曲"""
        distortions = []
        message_lower = message.lower()

        for distortion, keywords in COGNITIVE_DISTORTION_KEYWORDS.items():
            score = 0.0
            matched_keywords = []

            for keyword in keywords:
                if keyword in message_lower:
                    score += 1.0
                    matched_keywords.append(keyword)

            if score > 0:
                # 计算严重程度（0.0-1.0）
                severity = min(1.0, score / len(keywords) * 3)
                distortions.append((distortion, severity))
                logger.debug(f"检测到认知扭曲 {distortion.value}: {matched_keywords}")

        # 按严重程度排序
        distortions.sort(key=lambda x: x[1], reverse=True)
        return distortions[:3]  # 最多返回3个主要扭曲

    def _identify_irrational_beliefs(
        self, message: str
    ) -> List[Tuple[IrrationalBelief, float]]:
        """识别非理性信念"""
        beliefs = []
        message_lower = message.lower()

        for belief, keywords in IRRATIONAL_BELIEF_KEYWORDS.items():
            score = 0.0

            for keyword in keywords:
                if keyword in message_lower:
                    score += 1.0

            if score > 0:
                intensity = min(1.0, score / len(keywords) * 2)
                beliefs.append((belief, intensity))

        beliefs.sort(key=lambda x: x[1], reverse=True)
        return beliefs[:2]  # 最多返回2个主要非理性信念

    def _extract_beliefs_and_thoughts(
        self, message: str, context: Optional[List[str]] = None
    ) -> Tuple[List[str], List[str]]:
        """提取核心信念和自动化思维"""

        if not self.api_key:
            return self._keyword_extract_beliefs_thoughts(message)

        try:
            system_prompt = """你是专业的CBT认知疗法师。请分析文本中的：
1. 核心信念（关于自己、他人、世界的深层信念）
2. 自动化思维（快速、自动出现的想法）

请返回JSON格式：
{
  "core_beliefs": ["信念1", "信念2"],
  "automatic_thoughts": ["想法1", "想法2"]
}"""

            context_text = ""
            if context:
                context_text = f"对话上下文：{' '.join(context[-3:])}\n"

            prompt = f"""{context_text}
分析以下文本的认知结构：
"{message}"

识别核心信念和自动化思维："""

            response = self._call_api(prompt, system_prompt)
            if response:
                try:
                    data = json.loads(response)
                    core_beliefs = data.get("core_beliefs", [])
                    automatic_thoughts = data.get("automatic_thoughts", [])
                    return core_beliefs, automatic_thoughts
                except json.JSONDecodeError:
                    logger.warning("API响应JSON解析失败")

        except Exception as e:
            logger.warning(f"API提取信念思维失败: {e}")

        return self._keyword_extract_beliefs_thoughts(message)

    def _keyword_extract_beliefs_thoughts(
        self, message: str
    ) -> Tuple[List[str], List[str]]:
        """基于关键词提取信念和思维"""
        core_belief_patterns = [
            "我是",
            "我不是",
            "别人都",
            "世界就是",
            "人生就是",
            "我总是",
            "我永远",
        ]

        automatic_thought_patterns = [
            "我想",
            "我觉得",
            "我担心",
            "我害怕",
            "我相信",
            "我认为",
        ]

        core_beliefs = []
        automatic_thoughts = []

        message_lower = message.lower()

        for pattern in core_belief_patterns:
            if pattern in message_lower:
                # 简单提取包含模式的句子
                sentences = message.split("。")
                for sentence in sentences:
                    if pattern in sentence.lower():
                        core_beliefs.append(sentence.strip())

        for pattern in automatic_thought_patterns:
            if pattern in message_lower:
                sentences = message.split("。")
                for sentence in sentences:
                    if pattern in sentence.lower():
                        automatic_thoughts.append(sentence.strip())

        return core_beliefs[:3], automatic_thoughts[:3]

    def generate_socratic_question(
        self, user_id: int, message: str, analysis_result: CognitiveAnalysisResult
    ) -> SocraticResponse:
        """生成苏格拉底式询问"""

        # 根据识别的认知扭曲选择问题类型
        if analysis_result.distortions:
            primary_distortion = analysis_result.distortions[0][0]
            question_type = self._select_question_type_for_distortion(
                primary_distortion
            )
        else:
            question_type = SocraticQuestionType.CLARIFICATION

        # 生成针对性问题
        question = self._generate_targeted_question(
            message, question_type, analysis_result
        )

        purpose = self._get_question_purpose(question_type)

        follow_up_suggestions = self._get_follow_up_suggestions(
            question_type, analysis_result
        )

        response = SocraticResponse(
            question_type=question_type,
            question=question,
            purpose=purpose,
            follow_up_suggestions=follow_up_suggestions,
        )

        # 记录苏格拉底式对话
        self._record_socratic_dialogue(user_id, response)

        return response

    def _select_question_type_for_distortion(
        self, distortion: CognitiveDistortion
    ) -> SocraticQuestionType:
        """为认知扭曲选择合适的问题类型"""
        mapping = {
            CognitiveDistortion.ALL_OR_NOTHING: SocraticQuestionType.PERSPECTIVE,
            CognitiveDistortion.OVERGENERALIZATION: SocraticQuestionType.EVIDENCE,
            CognitiveDistortion.MENTAL_FILTER: SocraticQuestionType.PERSPECTIVE,
            CognitiveDistortion.JUMPING_TO_CONCLUSIONS: SocraticQuestionType.EVIDENCE,
            CognitiveDistortion.MAGNIFICATION: SocraticQuestionType.PERSPECTIVE,
            CognitiveDistortion.EMOTIONAL_REASONING: SocraticQuestionType.ASSUMPTION,
            CognitiveDistortion.SHOULD_STATEMENTS: SocraticQuestionType.CLARIFICATION,
            CognitiveDistortion.LABELING: SocraticQuestionType.EVIDENCE,
            CognitiveDistortion.PERSONALIZATION: SocraticQuestionType.ASSUMPTION,
        }
        return mapping.get(distortion, SocraticQuestionType.CLARIFICATION)

    def _generate_targeted_question(
        self,
        message: str,
        question_type: SocraticQuestionType,
        analysis_result: CognitiveAnalysisResult,
    ) -> str:
        """生成针对性的苏格拉底式问题"""

        templates = SOCRATIC_QUESTION_TEMPLATES.get(question_type, [])
        if not templates:
            return "能告诉我更多关于这个想法的细节吗？"

        # 提取关键短语
        key_phrases = []
        if analysis_result.automatic_thoughts:
            key_phrases.extend(analysis_result.automatic_thoughts[:2])
        if analysis_result.core_beliefs:
            key_phrases.extend(analysis_result.core_beliefs[:1])

        # 选择合适的模板并个性化
        import random

        template = random.choice(templates)

        if "{key_phrase}" in template and key_phrases:
            key_phrase = key_phrases[0]
            return template.format(key_phrase=key_phrase)

        return template

    def _get_question_purpose(self, question_type: SocraticQuestionType) -> str:
        """获取问题目的"""
        purposes = {
            SocraticQuestionType.CLARIFICATION: "澄清想法的具体含义",
            SocraticQuestionType.ASSUMPTION: "检查潜在假设的合理性",
            SocraticQuestionType.EVIDENCE: "审视支持想法的证据",
            SocraticQuestionType.PERSPECTIVE: "从不同角度看待问题",
            SocraticQuestionType.IMPLICATION: "探索想法的后续影响",
            SocraticQuestionType.META_QUESTION: "反思思维过程本身",
        }
        return purposes.get(question_type, "促进深度思考")

    def generate_cognitive_restructuring(
        self,
        user_id: int,
        original_thought: str,
        analysis_result: CognitiveAnalysisResult,
    ) -> Dict[str, Any]:
        """生成认知重构建议"""

        try:
            # 识别主要认知扭曲
            primary_distortions = [d[0] for d in analysis_result.distortions[:2]]

            # 生成重构建议
            restructured_thoughts = []
            techniques_used = []

            for distortion in primary_distortions:
                technique, restructured = self._restructure_for_distortion(
                    original_thought, distortion
                )
                if restructured:
                    restructured_thoughts.append(restructured)
                    techniques_used.append(technique)

            # 生成平衡性思维
            balanced_thought = self._generate_balanced_thought(
                original_thought, restructured_thoughts
            )

            restructuring_result = {
                "original_thought": original_thought,
                "identified_distortions": [d.value for d in primary_distortions],
                "restructured_thoughts": restructured_thoughts,
                "techniques_used": techniques_used,
                "balanced_thought": balanced_thought,
                "practice_exercises": self._generate_practice_exercises(
                    primary_distortions
                ),
            }

            # 存储认知重构记录
            if restructured_thoughts:
                self._store_cognitive_restructuring(
                    user_id,
                    original_thought,
                    balanced_thought,
                    ", ".join(techniques_used),
                )

            return restructuring_result

        except Exception as e:
            logger.error(f"认知重构生成失败: {e}")
            return {
                "original_thought": original_thought,
                "error": "重构生成失败",
                "balanced_thought": "让我们尝试从另一个角度来看这个问题。",
            }

    def _restructure_for_distortion(
        self, thought: str, distortion: CognitiveDistortion
    ) -> Tuple[str, str]:
        """为特定认知扭曲生成重构"""

        restructuring_strategies = {
            CognitiveDistortion.ALL_OR_NOTHING: (
                "连续性思维",
                f"将'{thought}'中的绝对化表达改为程度性表达，寻找中间地带。",
            ),
            CognitiveDistortion.OVERGENERALIZATION: (
                "具体化技术",
                f"将'{thought}'中的泛化表达限制在具体情境中。",
            ),
            CognitiveDistortion.MENTAL_FILTER: (
                "平衡性关注",
                f"除了'{thought}'提到的负面方面，还有哪些积极或中性的方面？",
            ),
            CognitiveDistortion.JUMPING_TO_CONCLUSIONS: (
                "证据检验",
                f"'{thought}'这个结论需要什么证据支持？有其他可能的解释吗？",
            ),
            CognitiveDistortion.MAGNIFICATION: (
                "比例调整",
                f"从1-10分来看，'{thought}'描述的情况实际严重程度是多少？",
            ),
            CognitiveDistortion.EMOTIONAL_REASONING: (
                "事实检验",
                f"除了'{thought}'中的感受，有什么客观事实可以参考？",
            ),
            CognitiveDistortion.SHOULD_STATEMENTS: (
                "偏好转换",
                f"将'{thought}'中的'应该'改为'我希望'或'我偏好'。",
            ),
            CognitiveDistortion.LABELING: (
                "行为描述",
                f"用具体行为描述代替'{thought}'中的标签化表达。",
            ),
            CognitiveDistortion.PERSONALIZATION: (
                "多因素分析",
                f"除了'{thought}'中提到的个人因素，还有哪些其他可能的原因？",
            ),
        }

        return restructuring_strategies.get(
            distortion, ("一般重构", "尝试从更平衡的角度看待这个想法。")
        )

    def _call_api(
        self, prompt: str, system_prompt: Optional[str] = None
    ) -> Optional[str]:
        """调用AI API"""
        if not self.api_key:
            return None

        try:
            # 构建请求数据
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }

            data = {
                "model": DEFAULT_MODEL,
                "messages": messages,
                "max_tokens": 300,
                "temperature": 0.3,
            }

            response = make_api_request(
                url=ZHIPUAI_API_ENDPOINT,
                method="POST",
                headers=headers,
                data=data,
                timeout=30,
            )

            if response and "choices" in response:
                return (
                    response["choices"][0].get("message", {}).get("content", "").strip()
                )

        except Exception as e:
            logger.error(f"API调用失败: {e}")

        return None

    def _analyze_emotional_patterns(self, message: str) -> Dict[str, float]:
        """分析情绪模式"""
        patterns = {
            "positive_emotion_level": 0.0,
            "negative_emotion_level": 0.0,
            "emotion_intensity": 0.0,
            "emotion_stability": 0.5,  # 默认中等稳定性
        }

        message_lower = message.lower()

        # 积极情感关键词
        positive_words = [
            "开心",
            "快乐",
            "高兴",
            "愉快",
            "满意",
            "喜悦",
            "幸福",
            "乐观",
            "希望",
        ]
        negative_words = [
            "难过",
            "伤心",
            "痛苦",
            "失望",
            "沮丧",
            "焦虑",
            "担心",
            "恐惧",
            "愤怒",
        ]

        positive_count = sum(1 for word in positive_words if word in message_lower)
        negative_count = sum(1 for word in negative_words if word in message_lower)

        total_words = len(message.split())
        if total_words > 0:
            patterns["positive_emotion_level"] = positive_count / total_words
            patterns["negative_emotion_level"] = negative_count / total_words
            patterns["emotion_intensity"] = (
                positive_count + negative_count
            ) / total_words

        return patterns

    def _identify_behavioral_patterns(self, message: str) -> List[str]:
        """识别行为模式"""
        patterns = []
        message_lower = message.lower()

        # 行为模式关键词
        avoidance_words = ["逃避", "躲避", "不想", "不敢", "害怕做"]
        activation_words = ["去做", "尝试", "努力", "坚持", "行动"]
        social_words = ["和朋友", "聚会", "交流", "分享", "合作"]

        if any(word in message_lower for word in avoidance_words):
            patterns.append("回避行为")

        if any(word in message_lower for word in activation_words):
            patterns.append("行为激活")

        if any(word in message_lower for word in social_words):
            patterns.append("社交行为")

        return patterns

    def _calculate_analysis_confidence(
        self,
        message: str,
        distortions: List[Tuple[CognitiveDistortion, float]],
        irrational_beliefs: List[Tuple[IrrationalBelief, float]],
        core_beliefs: List[str],
    ) -> float:
        """计算分析置信度"""
        confidence = 0.5  # 基础置信度

        # 基于消息长度调整
        if len(message) > 20:
            confidence += 0.1
        if len(message) > 50:
            confidence += 0.1

        # 基于检测到的模式数量调整
        if distortions:
            confidence += 0.1
        if irrational_beliefs:
            confidence += 0.1
        if core_beliefs:
            confidence += 0.1

        return min(1.0, confidence)

    def _get_follow_up_suggestions(
        self,
        question_type: SocraticQuestionType,
        analysis_result: CognitiveAnalysisResult,
    ) -> List[str]:
        """获取后续建议"""
        suggestions = []

        if question_type == SocraticQuestionType.CLARIFICATION:
            suggestions = [
                "可以给出更具体的例子",
                "描述当时的具体情况",
                "说明这种想法的细节",
            ]
        elif question_type == SocraticQuestionType.EVIDENCE:
            suggestions = [
                "寻找支持这个想法的证据",
                "考虑反驳这个想法的证据",
                "客观评估现有证据",
            ]
        elif question_type == SocraticQuestionType.PERSPECTIVE:
            suggestions = [
                "从朋友的角度看待这个问题",
                "考虑其他可能的解释",
                "想象五年后的自己会如何看待",
            ]
        else:
            suggestions = ["深入思考这个问题", "寻找更多的信息", "考虑不同的角度"]

        return suggestions

    def _generate_balanced_thought(
        self, original_thought: str, restructured_thoughts: List[str]
    ) -> str:
        """生成平衡性思维"""
        if not restructured_thoughts:
            return "让我们尝试从更平衡的角度来看这个问题。"

        return f"虽然{original_thought[:20]}...，但是我们也可以考虑：{restructured_thoughts[0][:50]}..."

    def _generate_practice_exercises(
        self, distortions: List[CognitiveDistortion]
    ) -> List[str]:
        """生成练习建议"""
        exercises = []

        for distortion in distortions:
            if distortion == CognitiveDistortion.ALL_OR_NOTHING:
                exercises.append(
                    "练习寻找中间地带：每当出现'总是'或'从不'的想法时，寻找例外情况"
                )
            elif distortion == CognitiveDistortion.OVERGENERALIZATION:
                exercises.append("具体化练习：将泛化的表述改为具体的情境描述")
            elif distortion == CognitiveDistortion.MENTAL_FILTER:
                exercises.append(
                    "平衡关注练习：每天记录一件积极的事情和一件需要改进的事情"
                )

        if not exercises:
            exercises.append("mindfulness练习：观察想法而不判断，培养觉察能力")

        return exercises[:3]  # 最多返回3个练习

    def _record_socratic_dialogue(self, user_id: int, response: SocraticResponse):
        """记录苏格拉底式对话"""
        try:
            self.db_manager.connect()
            self.db_manager.cursor.execute(
                """
                INSERT INTO socratic_dialogue
                (user_id, question_type, question_text)
                VALUES (?, ?, ?)
                """,
                (user_id, response.question_type.value, response.question),
            )
            self.db_manager.connection.commit()
            self.db_manager.disconnect()
        except Exception as e:
            logger.error(f"记录苏格拉底式对话失败: {e}")

    def _store_cognitive_analysis(
        self, user_id: int, message: str, result: CognitiveAnalysisResult
    ):
        """存储认知分析结果"""
        try:
            self.db_manager.connect()

            # 将结果转换为JSON字符串
            import json

            distortions_json = json.dumps(
                [(d[0].value, d[1]) for d in result.distortions]
            )
            beliefs_json = json.dumps(
                [(b[0].value, b[1]) for b in result.irrational_beliefs]
            )
            core_beliefs_json = json.dumps(result.core_beliefs)
            automatic_thoughts_json = json.dumps(result.automatic_thoughts)

            self.db_manager.cursor.execute(
                """
                INSERT INTO cognitive_analysis
                (user_id, message_text, distortions, irrational_beliefs,
                 core_beliefs, automatic_thoughts, confidence_score)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    message,
                    distortions_json,
                    beliefs_json,
                    core_beliefs_json,
                    automatic_thoughts_json,
                    result.confidence,
                ),
            )
            self.db_manager.connection.commit()
            self.db_manager.disconnect()
        except Exception as e:
            logger.error(f"存储认知分析结果失败: {e}")

    def _store_cognitive_restructuring(
        self,
        user_id: int,
        original_thought: str,
        restructured_thought: str,
        technique: str,
    ):
        """存储认知重构记录"""
        try:
            self.db_manager.connect()
            self.db_manager.cursor.execute(
                """
                INSERT INTO cognitive_restructuring
                (user_id, original_thought, restructured_thought, technique_used)
                VALUES (?, ?, ?, ?)
                """,
                (user_id, original_thought, restructured_thought, technique),
            )
            self.db_manager.connection.commit()
            self.db_manager.disconnect()
        except Exception as e:
            logger.error(f"存储认知重构记录失败: {e}")

    def store_message(
        self, user_id: int, message: str, response: str = "", emotion_detected: str = ""
    ):
        """存储对话消息到数据库（向后兼容方法）"""
        try:
            self.db_manager.connect()

            # 存储用户消息
            self.db_manager.cursor.execute(
                """
                INSERT INTO conversation_history
                (user_id, message, is_user, emotion_score, topic)
                VALUES (?, ?, ?, ?, ?)
                """,
                (user_id, message, 1, 0.5, emotion_detected or "neutral"),
            )

            # 如果有回复，也存储回复
            if response:
                self.db_manager.cursor.execute(
                    """
                    INSERT INTO conversation_history
                    (user_id, message, is_user, emotion_score, topic)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (user_id, response, 0, 0.5, "ai_response"),
                )

            self.db_manager.connection.commit()
            self.db_manager.disconnect()

        except Exception as e:
            logger.error(f"存储对话消息失败: {e}")

    def get_conversation_history(
        self, user_id: int, limit: int = 50, context_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """获取对话历史"""
        try:
            self.db_manager.connect()

            # 构建查询
            if context_id:
                query = """
                    SELECT id, message, is_user, timestamp, context_id, topic, emotion_score
                    FROM conversation_history
                    WHERE user_id = ? AND context_id = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                """
                params = (user_id, context_id, limit)
            else:
                query = """
                    SELECT id, message, is_user, timestamp, context_id, topic, emotion_score
                    FROM conversation_history
                    WHERE user_id = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                """
                params = (user_id, limit)

            self.db_manager.cursor.execute(query, params)
            rows = self.db_manager.cursor.fetchall()
            self.db_manager.disconnect()

            # 转换为标准格式
            messages = []
            for row in rows:
                message = {
                    "id": row[0],
                    "content": row[1],
                    "role": "user" if row[2] == 1 else "assistant",
                    "timestamp": row[3],
                    "context_id": row[4],
                    "topic": row[5],
                    "emotion_score": row[6],
                }
                messages.append(message)

            # 按时间正序返回（最早的在前）
            return list(reversed(messages))

        except Exception as e:
            logger.error(f"获取对话历史失败: {e}")
            return []

    def get_psychological_profile(self, user_id: int) -> Optional[Dict[str, Any]]:
        """获取用户心理画像（简化版本）"""
        try:
            # 简化的心理画像，基于最近的认知分析
            self.db_manager.connect()

            self.db_manager.cursor.execute(
                """
                SELECT distortions, irrational_beliefs, confidence_score
                FROM cognitive_analysis
                WHERE user_id = ?
                ORDER BY analysis_timestamp DESC
                LIMIT 5
                """,
                (user_id,),
            )

            rows = self.db_manager.cursor.fetchall()
            self.db_manager.disconnect()

            if not rows:
                return None

            # 构建简化的心理画像
            profile = {
                "personality_traits": {"extraversion": "medium"},
                "communication_preferences": {"formality": "casual"},
                "emotional_state": {"current_mood": "neutral"},
                "confidence_score": sum(row[2] for row in rows) / len(rows),
                "last_updated": datetime.now().isoformat(),
            }

            return profile

        except Exception as e:
            logger.error(f"获取心理画像失败: {e}")
            return None

    def generate_dialogue_with_style(
        self, user_id: int, prompt: str, context_id: Optional[str] = None
    ) -> Tuple[str, str]:
        """生成带风格的对话"""
        try:
            # 使用API生成对话
            if not self.api_key:
                # 没有API时的回退对话
                return (
                    "很抱歉，我现在无法访问AI服务。",
                    context_id or f"ctx_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                )

            # 调用AI API生成对话
            system_prompt = """你是'Kai'，善行伴侣应用中友好、乐观且略带好奇的虚拟宠物。
你的目标是鼓励用户并让他们感到被支持。
保持回应简洁（1-2句话），温暖自然，像真正的伙伴一样。
避免空洞的套话。尝试与具体事件建立联系。"""

            response = self._call_api(prompt, system_prompt)

            if response:
                generated_context_id = (
                    context_id or f"ctx_{datetime.now().strftime('%Y%m%d%H%M%S')}"
                )
                return response, generated_context_id
            else:
                return (
                    "我现在有点困惑，但我在这里陪着你！",
                    context_id or f"ctx_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                )

        except Exception as e:
            logger.error(f"生成对话失败: {e}")
            return (
                "... (The pet seems lost in thought)",
                context_id or f"ctx_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            )

    def cleanup_old_conversations(self, days_old: int = 30):
        """清理旧对话记录"""
        try:
            self.db_manager.connect()
            self.db_manager.cursor.execute(
                """
                DELETE FROM conversation_history
                WHERE timestamp < datetime('now', '-{} days')
                """.format(
                    days_old
                )
            )
            self.db_manager.connection.commit()
            self.db_manager.disconnect()
            logger.info(f"清理了{days_old}天前的对话记录")
        except Exception as e:
            logger.error(f"清理对话记录失败: {e}")

    def analyze_user_psychology(self, user_id: int) -> Optional[Dict[str, Any]]:
        """分析用户心理特征（简化版本）"""
        try:
            # 获取最近的对话历史
            messages = self.get_conversation_history(user_id, limit=20)

            if not messages:
                return None

            # 简化的心理分析
            user_messages = [msg for msg in messages if msg["role"] == "user"]

            if not user_messages:
                return None

            # 基于消息内容进行简单分析
            total_length = sum(len(msg["content"]) for msg in user_messages)
            avg_length = total_length / len(user_messages) if user_messages else 0

            # 构建心理画像
            profile = {
                "personality_traits": {
                    "extraversion": "high" if avg_length > 50 else "medium",
                    "openness": "high",
                },
                "communication_preferences": {
                    "formality": "casual",
                    "verbosity": "high" if avg_length > 50 else "medium",
                },
                "emotional_state": {"current_mood": "positive"},
                "confidence_score": 0.6,
                "last_updated": datetime.now().isoformat(),
            }

            # 存储心理画像（简化版本，这里只记录日志）
            logger.info(
                f"为用户{user_id}生成了心理画像，置信度: {profile['confidence_score']}"
            )

            return profile

        except Exception as e:
            logger.error(f"分析用户心理失败: {e}")
            return None


# 为了向后兼容，添加别名
ConversationAnalyzer = CBTConversationAnalyzer
