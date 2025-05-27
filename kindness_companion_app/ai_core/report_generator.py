"""
基于PERMA模型的智能报告生成系统

本模块实现以下功能：
1. 基于Martin Seligman的PERMA幸福模型进行心理健康评估
2. 多维度心理状态分析和可视化报告生成
3. 个性化成长建议和干预策略推荐
4. 心理健康趋势追踪和预测分析
5. 循证心理学原理的应用和验证
"""

import logging
import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import statistics
import math

from .emotion_analyzer import EmotionState, emotion_analyzer
from .conversation_analyzer import CognitiveAnalysisResult

logger = logging.getLogger(__name__)


# PERMA模型的五个维度
class PERMADimension(Enum):
    """Martin Seligman PERMA幸福模型的五个维度"""

    POSITIVE_EMOTION = "positive_emotion"  # 积极情感
    ENGAGEMENT = "engagement"  # 投入感
    RELATIONSHIPS = "relationships"  # 积极关系
    MEANING = "meaning"  # 人生意义
    ACHIEVEMENT = "achievement"  # 成就感


@dataclass
class PERMAScore:
    """PERMA各维度得分"""

    positive_emotion: float  # 0.0-10.0
    engagement: float  # 0.0-10.0
    relationships: float  # 0.0-10.0
    meaning: float  # 0.0-10.0
    achievement: float  # 0.0-10.0
    overall_wellbeing: float  # 总体幸福感得分

    def to_dict(self) -> Dict[str, float]:
        """转换为字典格式"""
        return {
            "positive_emotion": self.positive_emotion,
            "engagement": self.engagement,
            "relationships": self.relationships,
            "meaning": self.meaning,
            "achievement": self.achievement,
            "overall_wellbeing": self.overall_wellbeing,
        }


@dataclass
class PsychologicalInsight:
    """心理学洞察"""

    category: str  # 洞察类别
    insight: str  # 具体洞察内容
    evidence: List[str]  # 支持证据
    confidence: float  # 置信度 (0.0-1.0)
    intervention_suggestions: List[str]  # 干预建议


@dataclass
class WellbeingReport:
    """综合心理健康报告"""

    user_id: int
    assessment_period: Tuple[datetime, datetime]  # 评估时间段
    perma_scores: PERMAScore
    psychological_insights: List[PsychologicalInsight]
    cognitive_patterns: Dict[str, Any]  # 认知模式分析
    emotional_trends: Dict[str, Any]  # 情感趋势分析
    growth_recommendations: List[str]  # 成长建议
    risk_factors: List[str]  # 风险因素
    protective_factors: List[str]  # 保护因素
    confidence_score: float  # 整体分析置信度
    generated_at: datetime


# PERMA评估的关键词映射
PERMA_KEYWORDS = {
    PERMADimension.POSITIVE_EMOTION: {
        "positive": [
            "开心",
            "快乐",
            "兴奋",
            "喜悦",
            "满足",
            "感激",
            "幸福",
            "愉快",
            "乐观",
            "希望",
        ],
        "negative": [
            "难过",
            "沮丧",
            "焦虑",
            "恐惧",
            "愤怒",
            "绝望",
            "痛苦",
            "烦躁",
            "担心",
            "失望",
        ],
    },
    PERMADimension.ENGAGEMENT: {
        "positive": [
            "专注",
            "投入",
            "心流",
            "沉浸",
            "热情",
            "认真",
            "全神贯注",
            "享受过程",
            "忘记时间",
        ],
        "negative": [
            "分心",
            "无聊",
            "漫无目的",
            "缺乏兴趣",
            "机械重复",
            "被动",
            "无精打采",
        ],
    },
    PERMADimension.RELATIONSHIPS: {
        "positive": [
            "朋友",
            "家人",
            "爱",
            "关怀",
            "支持",
            "理解",
            "陪伴",
            "分享",
            "信任",
            "亲密",
            "归属感",
        ],
        "negative": [
            "孤独",
            "隔离",
            "冲突",
            "误解",
            "背叛",
            "拒绝",
            "疏远",
            "争吵",
            "孤单",
            "被忽视",
        ],
    },
    PERMADimension.MEANING: {
        "positive": [
            "意义",
            "目标",
            "价值",
            "使命",
            "贡献",
            "帮助他人",
            "有意义",
            "价值观",
            "理想",
            "信念",
        ],
        "negative": [
            "无意义",
            "空虚",
            "迷茫",
            "无目标",
            "浪费时间",
            "没有价值",
            "困惑",
            "不知道为什么",
        ],
    },
    PERMADimension.ACHIEVEMENT: {
        "positive": [
            "成功",
            "完成",
            "达成",
            "进步",
            "成长",
            "突破",
            "实现",
            "成就",
            "胜利",
            "提升",
            "掌握",
        ],
        "negative": [
            "失败",
            "挫折",
            "停滞",
            "退步",
            "无能",
            "做不到",
            "放弃",
            "失去信心",
            "能力不足",
        ],
    },
}

# 基于积极心理学的干预策略
POSITIVE_PSYCHOLOGY_INTERVENTIONS = {
    PERMADimension.POSITIVE_EMOTION: [
        "每日感恩练习：每天记录三件值得感恩的事情",
        "积极回忆法：回顾并品味美好的经历和成就",
        "微笑练习：有意识地增加微笑频率",
        "积极想象：想象美好的未来情景",
        "kindness acts：每天做一件善意的小事",
    ],
    PERMADimension.ENGAGEMENT: [
        "发现并运用个人优势：识别并在日常生活中应用你的核心优势",
        "心流活动：寻找让你全神贯注、忘记时间的活动",
        "技能挑战匹配：确保任务难度与你的技能水平相匹配",
        "深度工作练习：培养长时间专注的能力",
        "正念练习：提高当下觉察能力",
    ],
    PERMADimension.RELATIONSHIPS: [
        "积极回应练习：对他人的好消息给予积极热情的回应",
        "感恩表达：向重要的人表达感谢和欣赏",
        "深度倾听：练习全身心地倾听他人",
        "社交技能训练：学习更好的沟通和人际交往技巧",
        "建立支持网络：主动寻求和提供社会支持",
    ],
    PERMADimension.MEANING: [
        "价值观澄清：明确你的核心价值观和人生目标",
        "意义制造：在日常活动中寻找更深层的意义",
        "利他行为：参与志愿服务或帮助他人的活动",
        "legacy项目：考虑你想为世界留下什么",
        "哲学反思：思考人生的大问题和存在的意义",
    ],
    PERMADimension.ACHIEVEMENT: [
        "SMART目标设定：制定具体、可测量、可达成的目标",
        "成长思维培养：相信能力是可以通过努力发展的",
        "小胜利庆祝：认可和庆祝小的进步和成就",
        "挑战分解：将大目标分解为可管理的小步骤",
        "resilience训练：培养面对挫折的恢复能力",
    ],
}


class PERMAReportGenerator:
    """基于PERMA模型的报告生成器"""

    def __init__(self, db_manager):
        """
        初始化PERMA报告生成器

        Args:
            db_manager: 数据库管理器实例
        """
        self.db_manager = db_manager
        self._ensure_tables_exist()

    def _ensure_tables_exist(self):
        """确保必要的数据库表存在"""
        self.db_manager.connect()

        # PERMA评估记录表
        self.db_manager.cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS perma_assessments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            positive_emotion_score FLOAT NOT NULL,
            engagement_score FLOAT NOT NULL,
            relationships_score FLOAT NOT NULL,
            meaning_score FLOAT NOT NULL,
            achievement_score FLOAT NOT NULL,
            overall_wellbeing_score FLOAT NOT NULL,
            assessment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            confidence_score FLOAT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        """
        )

        # 心理健康报告表
        self.db_manager.cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS wellbeing_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            report_data TEXT NOT NULL,  -- JSON字符串存储完整报告
            report_period_start TIMESTAMP NOT NULL,
            report_period_end TIMESTAMP NOT NULL,
            generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            confidence_score FLOAT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        """
        )

        # 干预建议跟踪表
        self.db_manager.cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS intervention_tracking (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            intervention_type TEXT NOT NULL,
            intervention_content TEXT NOT NULL,
            suggested_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_date TIMESTAMP,
            effectiveness_rating INTEGER,  -- 1-5评分
            user_feedback TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        """
        )

        self.db_manager.connection.commit()
        self.db_manager.disconnect()

    def generate_comprehensive_report(
        self, user_id: int, days_back: int = 30
    ) -> WellbeingReport:
        """
        生成综合心理健康报告

        Args:
            user_id: 用户ID
            days_back: 回溯分析的天数

        Returns:
            WellbeingReport: 综合心理健康报告
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)

        try:
            # 1. 收集用户数据
            user_data = self._collect_user_data(user_id, start_date, end_date)

            # 2. 进行PERMA评估
            perma_scores = self._assess_perma_dimensions(user_data)

            # 3. 生成心理学洞察
            psychological_insights = self._generate_psychological_insights(
                user_data, perma_scores
            )

            # 4. 分析认知模式
            cognitive_patterns = self._analyze_cognitive_patterns(user_data)

            # 5. 分析情感趋势
            emotional_trends = self._analyze_emotional_trends(user_data)

            # 6. 生成个性化建议
            growth_recommendations = self._generate_growth_recommendations(
                perma_scores, user_data
            )

            # 7. 识别风险和保护因素
            risk_factors, protective_factors = self._identify_risk_protective_factors(
                user_data, perma_scores
            )

            # 8. 计算整体置信度
            confidence_score = self._calculate_overall_confidence(
                user_data, perma_scores
            )

            # 9. 构建报告
            report = WellbeingReport(
                user_id=user_id,
                assessment_period=(start_date, end_date),
                perma_scores=perma_scores,
                psychological_insights=psychological_insights,
                cognitive_patterns=cognitive_patterns,
                emotional_trends=emotional_trends,
                growth_recommendations=growth_recommendations,
                risk_factors=risk_factors,
                protective_factors=protective_factors,
                confidence_score=confidence_score,
                generated_at=datetime.now(),
            )

            # 10. 存储报告
            self._store_report(report)

            logger.info(
                f"生成用户{user_id}的综合心理健康报告，整体幸福感得分: {perma_scores.overall_wellbeing:.2f}"
            )
            return report

        except Exception as e:
            logger.error(f"生成综合报告失败: {e}")
            # 返回默认报告
            return self._create_default_report(user_id, start_date, end_date)

    def _collect_user_data(
        self, user_id: int, start_date: datetime, end_date: datetime
    ) -> Dict[str, Any]:
        """收集用户在指定时间段内的所有相关数据"""

        data = {
            "messages": [],
            "emotions": [],
            "cognitive_analyses": [],
            "conversations": [],
            "activities": [],
            "metadata": {
                "total_interactions": 0,
                "active_days": 0,
                "avg_daily_interactions": 0,
            },
        }

        try:
            # 收集对话消息
            messages = self.db_manager.execute_query(
                """
                SELECT message, timestamp, emotion_score, topic
                FROM conversation_history
                WHERE user_id = ? AND timestamp BETWEEN ? AND ?
                ORDER BY timestamp ASC
                """,
                (user_id, start_date, end_date),
            )
            data["messages"] = messages or []

            # 收集情感分析数据
            emotions = emotion_analyzer.get_emotion_trajectory(user_id)
            data["emotions"] = emotions[-100:]  # 最近100条情感记录

            # 收集认知分析数据
            cognitive_data = self.db_manager.execute_query(
                """
                SELECT message_text, distortions, irrational_beliefs,
                       core_beliefs, automatic_thoughts, confidence_score, analysis_timestamp
                FROM cognitive_analysis
                WHERE user_id = ? AND analysis_timestamp BETWEEN ? AND ?
                ORDER BY analysis_timestamp ASC
                """,
                (user_id, start_date, end_date),
            )
            data["cognitive_analyses"] = cognitive_data or []

            # 计算元数据
            data["metadata"]["total_interactions"] = len(data["messages"])
            if data["messages"]:
                dates = set(
                    msg["timestamp"][:10] for msg in data["messages"]
                )  # 提取日期部分
                data["metadata"]["active_days"] = len(dates)
                data["metadata"]["avg_daily_interactions"] = data["metadata"][
                    "total_interactions"
                ] / max(1, data["metadata"]["active_days"])

        except Exception as e:
            logger.error(f"收集用户数据失败: {e}")

        return data

    def _assess_perma_dimensions(self, user_data: Dict[str, Any]) -> PERMAScore:
        """基于PERMA模型评估各维度得分"""

        dimension_scores = {}

        # 分析每个PERMA维度
        for dimension in PERMADimension:
            score = self._calculate_dimension_score(dimension, user_data)
            dimension_scores[dimension.value] = score

        # 计算总体幸福感得分（加权平均）
        weights = {
            PERMADimension.POSITIVE_EMOTION: 0.25,
            PERMADimension.ENGAGEMENT: 0.20,
            PERMADimension.RELATIONSHIPS: 0.25,
            PERMADimension.MEANING: 0.15,
            PERMADimension.ACHIEVEMENT: 0.15,
        }

        overall_wellbeing = sum(
            dimension_scores[dim.value] * weights[dim] for dim in PERMADimension
        )

        return PERMAScore(
            positive_emotion=dimension_scores[PERMADimension.POSITIVE_EMOTION.value],
            engagement=dimension_scores[PERMADimension.ENGAGEMENT.value],
            relationships=dimension_scores[PERMADimension.RELATIONSHIPS.value],
            meaning=dimension_scores[PERMADimension.MEANING.value],
            achievement=dimension_scores[PERMADimension.ACHIEVEMENT.value],
            overall_wellbeing=overall_wellbeing,
        )

    def _calculate_dimension_score(
        self, dimension: PERMADimension, user_data: Dict[str, Any]
    ) -> float:
        """计算单个PERMA维度的得分"""

        positive_keywords = PERMA_KEYWORDS[dimension]["positive"]
        negative_keywords = PERMA_KEYWORDS[dimension]["negative"]

        positive_count = 0
        negative_count = 0
        total_words = 0

        # 分析消息中的关键词
        for message in user_data["messages"]:
            text = message.get("message", "").lower()
            words = text.split()
            total_words += len(words)

            for word in words:
                if any(keyword in word for keyword in positive_keywords):
                    positive_count += 1
                elif any(keyword in word for keyword in negative_keywords):
                    negative_count += 1

        # 基础得分计算
        if total_words == 0:
            base_score = 5.0  # 默认中性得分
        else:
            # 计算正负面关键词比例
            positive_ratio = positive_count / max(1, total_words)
            negative_ratio = negative_count / max(1, total_words)

            # 转换为0-10分制
            base_score = 5.0 + (positive_ratio - negative_ratio) * 100
            base_score = max(0.0, min(10.0, base_score))

        # 根据情感数据调整得分
        if dimension == PERMADimension.POSITIVE_EMOTION:
            base_score = self._adjust_for_emotions(base_score, user_data["emotions"])

        # 根据认知分析调整得分
        if user_data["cognitive_analyses"]:
            base_score = self._adjust_for_cognitive_patterns(
                base_score, dimension, user_data["cognitive_analyses"]
            )

        return round(base_score, 2)

    def _adjust_for_emotions(
        self, base_score: float, emotions: List[EmotionState]
    ) -> float:
        """根据情感数据调整积极情感维度得分"""
        if not emotions:
            return base_score

        # 计算积极情感比例
        positive_emotions = ["joy", "trust", "anticipation"]
        recent_emotions = emotions[-20:]  # 最近20条情感记录

        positive_count = sum(
            1
            for emotion in recent_emotions
            if emotion.primary_emotion.value in positive_emotions
        )

        positive_ratio = positive_count / len(recent_emotions)

        # 调整得分
        adjustment = (positive_ratio - 0.5) * 4  # -2到+2的调整范围
        adjusted_score = base_score + adjustment

        return max(0.0, min(10.0, adjusted_score))

    def _adjust_for_cognitive_patterns(
        self,
        base_score: float,
        dimension: PERMADimension,
        cognitive_analyses: List[Dict[str, Any]],
    ) -> float:
        """根据认知模式调整维度得分"""
        if not cognitive_analyses:
            return base_score

        # 计算认知扭曲严重程度
        total_distortions = 0
        for analysis in cognitive_analyses[-10:]:  # 最近10次分析
            distortions_data = analysis.get("distortions", "[]")
            try:
                distortions = json.loads(distortions_data) if distortions_data else []
                total_distortions += len(distortions)
            except json.JSONDecodeError:
                continue

        avg_distortions = total_distortions / len(cognitive_analyses[-10:])

        # 根据认知扭曲程度调整得分
        distortion_penalty = min(2.0, avg_distortions * 0.5)
        adjusted_score = base_score - distortion_penalty

        return max(0.0, min(10.0, adjusted_score))

    def _generate_psychological_insights(
        self, user_data: Dict[str, Any], perma_scores: PERMAScore
    ) -> List[PsychologicalInsight]:
        """生成基于数据的心理学洞察"""

        insights = []

        # 分析PERMA维度的强项和弱项
        scores_dict = perma_scores.to_dict()
        max_dimension = max(scores_dict.items(), key=lambda x: x[1])
        min_dimension = min(scores_dict.items(), key=lambda x: x[1])

        # 强项洞察
        if max_dimension[1] >= 7.0:
            insights.append(
                PsychologicalInsight(
                    category="优势识别",
                    insight=f"你在{self._translate_dimension(max_dimension[0])}方面表现出色（得分: {max_dimension[1]:.1f}），这是你的重要心理资源。",
                    evidence=[f"在相关对话中表现出积极的态度和体验"],
                    confidence=0.8,
                    intervention_suggestions=POSITIVE_PSYCHOLOGY_INTERVENTIONS.get(
                        self._get_dimension_enum(max_dimension[0]), []
                    )[:2],
                )
            )

        # 发展空间洞察
        if min_dimension[1] <= 4.0:
            insights.append(
                PsychologicalInsight(
                    category="发展机会",
                    insight=f"你在{self._translate_dimension(min_dimension[0])}方面有较大发展空间（得分: {min_dimension[1]:.1f}）。",
                    evidence=[f"相关表达中较少出现积极内容"],
                    confidence=0.7,
                    intervention_suggestions=POSITIVE_PSYCHOLOGY_INTERVENTIONS.get(
                        self._get_dimension_enum(min_dimension[0]), []
                    )[:3],
                )
            )

        # 整体幸福感洞察
        if perma_scores.overall_wellbeing >= 7.0:
            insights.append(
                PsychologicalInsight(
                    category="整体评估",
                    insight=f"你的整体心理幸福感处于良好水平（得分: {perma_scores.overall_wellbeing:.1f}），继续保持这些积极的生活模式。",
                    evidence=["多个PERMA维度得分较高"],
                    confidence=0.9,
                    intervention_suggestions=[
                        "继续现有的积极实践",
                        "可以尝试帮助他人提升幸福感",
                    ],
                )
            )
        elif perma_scores.overall_wellbeing <= 4.0:
            insights.append(
                PsychologicalInsight(
                    category="关注建议",
                    insight=f"你的整体心理幸福感需要关注（得分: {perma_scores.overall_wellbeing:.1f}），建议从多个维度进行改善。",
                    evidence=["多个PERMA维度得分偏低"],
                    confidence=0.8,
                    intervention_suggestions=[
                        "寻求专业心理健康支持",
                        "建立规律的自我关怀实践",
                        "加强社会支持网络",
                    ],
                )
            )

        return insights

    def _analyze_emotional_trends(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """分析情感趋势"""

        trends = {
            "dominant_emotions": [],
            "emotion_stability": 0.0,
            "positive_emotion_ratio": 0.0,
            "emotion_complexity": 0.0,
            "recent_trend": "stable",  # stable, improving, declining
        }

        emotions = user_data["emotions"]
        if not emotions:
            return trends

        # 分析主导情感
        emotion_counts = {}
        for emotion in emotions:
            emotion_name = emotion.primary_emotion.value
            emotion_counts[emotion_name] = emotion_counts.get(emotion_name, 0) + 1

        sorted_emotions = sorted(
            emotion_counts.items(), key=lambda x: x[1], reverse=True
        )
        trends["dominant_emotions"] = [
            {"emotion": e[0], "frequency": e[1]} for e in sorted_emotions[:3]
        ]

        # 计算情感稳定性（方差越小越稳定）
        if len(emotions) > 1:
            valence_scores = [e.dimensions.valence for e in emotions]
            trends["emotion_stability"] = 1.0 / (
                1.0 + statistics.variance(valence_scores)
            )

        # 计算积极情感比例
        positive_emotions = ["joy", "trust", "anticipation"]
        positive_count = sum(
            1 for e in emotions if e.primary_emotion.value in positive_emotions
        )
        trends["positive_emotion_ratio"] = positive_count / len(emotions)

        # 分析最近趋势
        if len(emotions) >= 10:
            recent_emotions = emotions[-5:]
            earlier_emotions = emotions[-10:-5]

            recent_valence = statistics.mean(
                e.dimensions.valence for e in recent_emotions
            )
            earlier_valence = statistics.mean(
                e.dimensions.valence for e in earlier_emotions
            )

            if recent_valence > earlier_valence + 0.2:
                trends["recent_trend"] = "improving"
            elif recent_valence < earlier_valence - 0.2:
                trends["recent_trend"] = "declining"

        return trends

    def _translate_dimension(self, dimension_key: str) -> str:
        """将PERMA维度英文转换为中文"""
        translations = {
            "positive_emotion": "积极情感",
            "engagement": "投入感",
            "relationships": "人际关系",
            "meaning": "人生意义",
            "achievement": "成就感",
        }
        return translations.get(dimension_key, dimension_key)

    def _get_dimension_enum(self, dimension_key: str) -> Optional[PERMADimension]:
        """根据字符串获取PERMA维度枚举"""
        mapping = {
            "positive_emotion": PERMADimension.POSITIVE_EMOTION,
            "engagement": PERMADimension.ENGAGEMENT,
            "relationships": PERMADimension.RELATIONSHIPS,
            "meaning": PERMADimension.MEANING,
            "achievement": PERMADimension.ACHIEVEMENT,
        }
        return mapping.get(dimension_key)

    def _store_report(self, report: WellbeingReport):
        """存储心理健康报告到数据库"""
        try:
            # 存储PERMA评估
            self.db_manager.execute_insert(
                """
                INSERT INTO perma_assessments
                (user_id, positive_emotion_score, engagement_score, relationships_score,
                 meaning_score, achievement_score, overall_wellbeing_score, confidence_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    report.user_id,
                    report.perma_scores.positive_emotion,
                    report.perma_scores.engagement,
                    report.perma_scores.relationships,
                    report.perma_scores.meaning,
                    report.perma_scores.achievement,
                    report.perma_scores.overall_wellbeing,
                    report.confidence_score,
                ),
            )

            # 存储完整报告
            report_json = json.dumps(
                {
                    "perma_scores": report.perma_scores.to_dict(),
                    "psychological_insights": [
                        {
                            "category": insight.category,
                            "insight": insight.insight,
                            "evidence": insight.evidence,
                            "confidence": insight.confidence,
                            "intervention_suggestions": insight.intervention_suggestions,
                        }
                        for insight in report.psychological_insights
                    ],
                    "cognitive_patterns": report.cognitive_patterns,
                    "emotional_trends": report.emotional_trends,
                    "growth_recommendations": report.growth_recommendations,
                    "risk_factors": report.risk_factors,
                    "protective_factors": report.protective_factors,
                },
                ensure_ascii=False,
                indent=2,
            )

            self.db_manager.execute_insert(
                """
                INSERT INTO wellbeing_reports
                (user_id, report_data, report_period_start, report_period_end, confidence_score)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    report.user_id,
                    report_json,
                    report.assessment_period[0],
                    report.assessment_period[1],
                    report.confidence_score,
                ),
            )

            logger.info(f"成功存储用户{report.user_id}的心理健康报告")

        except Exception as e:
            logger.error(f"存储报告失败: {e}")

    def _analyze_cognitive_patterns(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """分析认知模式"""
        patterns = {
            "common_distortions": [],
            "thinking_flexibility": 0.0,
            "cognitive_bias_severity": 0.0,
            "rational_thinking_score": 0.0,
        }

        cognitive_analyses = user_data.get("cognitive_analyses", [])
        if not cognitive_analyses:
            return patterns

        # 分析常见认知扭曲
        distortion_counts = {}
        total_analyses = len(cognitive_analyses)

        for analysis in cognitive_analyses:
            distortions_data = analysis.get("distortions", "[]")
            try:
                distortions = json.loads(distortions_data) if distortions_data else []
                for distortion_info in distortions:
                    if isinstance(distortion_info, list) and len(distortion_info) >= 2:
                        distortion_type = distortion_info[0]
                        severity = distortion_info[1]
                        distortion_counts[distortion_type] = (
                            distortion_counts.get(distortion_type, 0) + severity
                        )
            except (json.JSONDecodeError, TypeError):
                continue

        # 获取最常见的认知扭曲
        if distortion_counts:
            sorted_distortions = sorted(
                distortion_counts.items(), key=lambda x: x[1], reverse=True
            )
            patterns["common_distortions"] = [
                {"type": d[0], "frequency": d[1] / total_analyses}
                for d in sorted_distortions[:3]
            ]

            # 计算认知偏差严重程度
            total_severity = sum(distortion_counts.values())
            patterns["cognitive_bias_severity"] = min(
                10.0, total_severity / total_analyses
            )

            # 计算理性思维得分（认知扭曲越少得分越高）
            patterns["rational_thinking_score"] = max(
                0.0, 10.0 - patterns["cognitive_bias_severity"]
            )

        return patterns

    def _generate_growth_recommendations(
        self, perma_scores: PERMAScore, user_data: Dict[str, Any]
    ) -> List[str]:
        """生成个性化成长建议"""
        recommendations = []

        # 基于PERMA得分的建议
        scores_dict = perma_scores.to_dict()

        # 针对得分较低的维度提供建议
        for dimension, score in scores_dict.items():
            if score < 5.0 and dimension != "overall_wellbeing":
                dimension_enum = self._get_dimension_enum(dimension)
                if dimension_enum:
                    interventions = POSITIVE_PSYCHOLOGY_INTERVENTIONS.get(
                        dimension_enum, []
                    )
                    recommendations.extend(interventions[:2])  # 每个维度最多2个建议

        # 基于认知模式的建议
        cognitive_patterns = user_data.get("cognitive_patterns", {})
        if cognitive_patterns.get("cognitive_bias_severity", 0) > 6.0:
            recommendations.extend(
                [
                    "练习认知重构技术：学会识别和挑战不合理的想法",
                    "建立客观思维：寻找支持和反驳想法的证据",
                    "mindfulness练习：提高对自动化思维的觉察",
                ]
            )

        # 基于情感趋势的建议
        emotional_trends = user_data.get("emotional_trends", {})
        if emotional_trends.get("positive_emotion_ratio", 0.5) < 0.3:
            recommendations.extend(
                [
                    "积极情感培养：每天记录一件让你感到快乐的事情",
                    "社会连接：主动联系一位重要的朋友或家人",
                    "self-compassion练习：对自己更加温和和理解",
                ]
            )

        # 去重并限制数量
        unique_recommendations = list(dict.fromkeys(recommendations))
        return unique_recommendations[:8]  # 最多8个建议

    def _identify_risk_protective_factors(
        self, user_data: Dict[str, Any], perma_scores: PERMAScore
    ) -> Tuple[List[str], List[str]]:
        """识别风险因素和保护因素"""
        risk_factors = []
        protective_factors = []

        # 基于PERMA得分识别
        if perma_scores.positive_emotion < 3.0:
            risk_factors.append("积极情感体验不足")
        elif perma_scores.positive_emotion > 7.0:
            protective_factors.append("丰富的积极情感体验")

        if perma_scores.relationships < 3.0:
            risk_factors.append("社会支持网络薄弱")
        elif perma_scores.relationships > 7.0:
            protective_factors.append("强大的社会支持网络")

        if perma_scores.meaning < 3.0:
            risk_factors.append("缺乏人生意义感")
        elif perma_scores.meaning > 7.0:
            protective_factors.append("清晰的人生目标和价值观")

        # 基于认知模式识别
        cognitive_patterns = user_data.get("cognitive_patterns", {})
        if cognitive_patterns.get("cognitive_bias_severity", 0) > 7.0:
            risk_factors.append("严重的认知扭曲模式")
        elif cognitive_patterns.get("rational_thinking_score", 0) > 7.0:
            protective_factors.append("良好的理性思维能力")

        # 基于情感趋势识别
        emotional_trends = user_data.get("emotional_trends", {})
        if emotional_trends.get("recent_trend") == "declining":
            risk_factors.append("近期情绪呈下降趋势")
        elif emotional_trends.get("recent_trend") == "improving":
            protective_factors.append("近期情绪呈改善趋势")

        if emotional_trends.get("emotion_stability", 0) > 0.7:
            protective_factors.append("良好的情绪稳定性")
        elif emotional_trends.get("emotion_stability", 0) < 0.3:
            risk_factors.append("情绪波动较大")

        return risk_factors, protective_factors

    def _calculate_overall_confidence(
        self, user_data: Dict[str, Any], perma_scores: PERMAScore
    ) -> float:
        """计算整体分析置信度"""
        confidence_factors = []

        # 数据量因素
        message_count = len(user_data.get("messages", []))
        if message_count >= 50:
            confidence_factors.append(0.9)
        elif message_count >= 20:
            confidence_factors.append(0.7)
        elif message_count >= 10:
            confidence_factors.append(0.5)
        else:
            confidence_factors.append(0.3)

        # 数据多样性因素
        emotion_count = len(user_data.get("emotions", []))
        cognitive_count = len(user_data.get("cognitive_analyses", []))

        if emotion_count >= 10 and cognitive_count >= 5:
            confidence_factors.append(0.8)
        elif emotion_count >= 5 or cognitive_count >= 3:
            confidence_factors.append(0.6)
        else:
            confidence_factors.append(0.4)

        # 时间跨度因素
        active_days = user_data.get("metadata", {}).get("active_days", 0)
        if active_days >= 14:
            confidence_factors.append(0.8)
        elif active_days >= 7:
            confidence_factors.append(0.6)
        else:
            confidence_factors.append(0.4)

        # 计算加权平均置信度
        overall_confidence = sum(confidence_factors) / len(confidence_factors)
        return round(overall_confidence, 2)

    def _create_default_report(
        self, user_id: int, start_date: datetime, end_date: datetime
    ) -> WellbeingReport:
        """创建默认报告（当数据不足时）"""
        default_perma = PERMAScore(
            positive_emotion=5.0,
            engagement=5.0,
            relationships=5.0,
            meaning=5.0,
            achievement=5.0,
            overall_wellbeing=5.0,
        )

        default_insight = PsychologicalInsight(
            category="数据不足",
            insight="由于互动数据较少，暂时无法提供详细的心理分析。建议继续使用系统以获得更准确的评估。",
            evidence=["互动次数较少"],
            confidence=0.2,
            intervention_suggestions=[
                "增加与系统的互动频率",
                "分享更多的想法和感受",
                "定期进行自我反思",
            ],
        )

        return WellbeingReport(
            user_id=user_id,
            assessment_period=(start_date, end_date),
            perma_scores=default_perma,
            psychological_insights=[default_insight],
            cognitive_patterns={},
            emotional_trends={},
            growth_recommendations=["继续与系统互动以获得个性化建议"],
            risk_factors=[],
            protective_factors=[],
            confidence_score=0.2,
            generated_at=datetime.now(),
        )


# 全局报告生成器实例（需要在使用时初始化）
_report_generator = None


def get_report_generator(db_manager):
    """获取全局报告生成器实例"""
    global _report_generator
    if _report_generator is None:
        _report_generator = PERMAReportGenerator(db_manager)
    return _report_generator


def generate_weekly_report(user_id: int, days_back: int = 7):
    """
    生成用户周报（向后兼容函数）

    Args:
        user_id: 用户ID
        days_back: 回溯天数，默认7天

    Returns:
        dict: 报告数据或错误信息
    """
    try:
        # 这里需要获取数据库管理器实例
        # 为了向后兼容，使用简化的实现
        from ..backend.database_manager import DatabaseManager

        db_manager = DatabaseManager()
        report_generator = get_report_generator(db_manager)

        # 生成综合报告
        report = report_generator.generate_comprehensive_report(user_id, days_back)

        # 转换为旧格式以保持兼容性
        return {
            "success": True,
            "user_id": user_id,
            "report_period": f"过去{days_back}天",
            "perma_scores": report.perma_scores.to_dict(),
            "insights": [
                {
                    "category": insight.category,
                    "content": insight.insight,
                    "confidence": insight.confidence,
                }
                for insight in report.psychological_insights
            ],
            "recommendations": report.growth_recommendations,
            "emotional_trends": report.emotional_trends,
            "cognitive_patterns": report.cognitive_patterns,
            "risk_factors": report.risk_factors,
            "protective_factors": report.protective_factors,
            "overall_wellbeing": report.perma_scores.overall_wellbeing,
            "confidence": report.confidence_score,
            "generated_at": report.generated_at.isoformat(),
        }

    except Exception as e:
        logger.error(f"生成周报失败: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "报告生成失败，请稍后重试",
        }
