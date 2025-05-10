import pytest
from kindness_companion_app.ai_core.pet_handler import PetHandler
from kindness_companion_app.ai_core.dialogue_generator import DialogueGenerator
from kindness_companion_app.ai_core.emotion_analyzer import EmotionAnalyzer


class TestPetHandler:
    def test_pet_initialization(self, db_manager):
        """测试宠物初始化"""
        pet_handler = PetHandler(db_manager)
        assert pet_handler is not None
        assert pet_handler.pet_name is not None
        assert pet_handler.personality is not None

    def test_pet_interaction(self, db_manager):
        """测试宠物交互"""
        pet_handler = PetHandler(db_manager)

        # 测试基本对话
        response = pet_handler.get_response("你好")
        assert response is not None
        assert len(response) > 0

        # 测试情感回应
        response = pet_handler.get_emotional_response("我很开心")
        assert response is not None
        assert len(response) > 0


class TestDialogueGenerator:
    def test_dialogue_generation(self):
        """测试对话生成"""
        generator = DialogueGenerator()

        # 测试基本对话生成
        dialogue = generator.generate_dialogue("今天天气真好")
        assert dialogue is not None
        assert len(dialogue) > 0

        # 测试上下文对话
        context = "用户正在完成一个善行挑战"
        dialogue = generator.generate_contextual_dialogue(context)
        assert dialogue is not None
        assert len(dialogue) > 0


class TestEmotionAnalyzer:
    def test_emotion_analysis(self):
        """测试情感分析"""
        analyzer = EmotionAnalyzer()

        # 测试积极情感
        emotion = analyzer.analyze_emotion("我今天帮助了一个老人过马路，感觉很开心")
        assert emotion is not None
        assert emotion["sentiment"] in ["positive", "neutral", "negative"]
        assert "confidence" in emotion

        # 测试消极情感
        emotion = analyzer.analyze_emotion("我今天没有完成挑战，感觉很沮丧")
        assert emotion is not None
        assert emotion["sentiment"] in ["positive", "neutral", "negative"]
        assert "confidence" in emotion

    def test_emotion_tracking(self, db_manager):
        """测试情感追踪"""
        analyzer = EmotionAnalyzer()

        # 记录情感变化
        user_id = 1
        emotion_data = {
            "sentiment": "positive",
            "confidence": 0.8,
            "timestamp": "2024-03-20 10:00:00",
        }

        # 保存情感数据
        analyzer.save_emotion_data(user_id, emotion_data)

        # 获取情感历史
        history = analyzer.get_emotion_history(user_id)
        assert len(history) > 0
        assert any(e["sentiment"] == "positive" for e in history)

    def test_emotion_recommendation(self, db_manager):
        """测试情感推荐"""
        analyzer = EmotionAnalyzer()

        # 测试基于情感的推荐
        user_id = 1
        recommendation = analyzer.get_emotion_based_recommendation(user_id)
        assert recommendation is not None
        assert "challenge" in recommendation
        assert "reason" in recommendation
