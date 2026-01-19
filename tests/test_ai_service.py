"""AI 서비스 테스트"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.services.ai_service import generate_quiz
from app.schemas.ai import AIQuizGenerationRequest, AIQuizGenerationResponse


@pytest.mark.asyncio
async def test_generate_quiz_success():
    """문제 생성 성공 테스트"""
    mock_response = MagicMock()
    mock_response.text = '{"question": "테스트 문제", "options": [{"index": 0, "text": "선택지1"}, {"index": 1, "text": "선택지2"}, {"index": 2, "text": "선택지3"}, {"index": 3, "text": "선택지4"}], "correct_answer": 0, "explanation": "설명"}'
    
    mock_client = MagicMock()
    mock_models = MagicMock()
    mock_models.generate_content = MagicMock(return_value=mock_response)
    mock_client.models = mock_models
    
    with patch("app.services.ai_service.get_gemini_client", return_value=mock_client):
        request = AIQuizGenerationRequest(
            source_text="테스트 텍스트",
            subject_name="데이터 분석",
        )
        result = await generate_quiz(request)
        
        assert isinstance(result, AIQuizGenerationResponse)
        assert result.question == "테스트 문제"
        assert len(result.options) == 4
        assert result.correct_answer == 0


@pytest.mark.asyncio
async def test_generate_quiz_empty_response():
    """AI 응답이 비어있는 경우"""
    mock_response = MagicMock()
    mock_response.text = None
    
    mock_client = MagicMock()
    mock_models = MagicMock()
    mock_models.generate_content = MagicMock(return_value=mock_response)
    mock_client.models = mock_models
    
    with patch("app.services.ai_service.get_gemini_client", return_value=mock_client):
        request = AIQuizGenerationRequest(
            source_text="테스트 텍스트",
            subject_name="데이터 분석",
        )
        
        with pytest.raises(ValueError, match="AI 응답이 비어있습니다"):
            await generate_quiz(request)
