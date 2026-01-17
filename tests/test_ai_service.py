"""AI 서비스 테스트"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.services.ai_service import get_openai_client, generate_quiz
from app.schemas.ai import AIQuizGenerationRequest, AIQuizGenerationResponse


def test_get_openai_client_singleton():
    """OpenAI 클라이언트 싱글톤 테스트"""
    from app.services.ai_service import _client
    import app.services.ai_service as ai_module
    
    ai_module._client = None
    client1 = get_openai_client()
    client2 = get_openai_client()
    
    assert client1 is client2


@pytest.mark.asyncio
async def test_generate_quiz_success():
    """문제 생성 성공 테스트"""
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = '{"question": "테스트 문제", "options": [{"index": 0, "text": "선택지1"}, {"index": 1, "text": "선택지2"}, {"index": 2, "text": "선택지3"}, {"index": 3, "text": "선택지4"}], "correct_answer": 0, "explanation": "설명"}'
    
    mock_client = AsyncMock()
    mock_client.beta.chat.completions.create = AsyncMock(return_value=mock_response)
    
    with patch("app.services.ai_service.get_openai_client", return_value=mock_client):
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
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = None
    
    mock_client = AsyncMock()
    mock_client.beta.chat.completions.create = AsyncMock(return_value=mock_response)
    
    with patch("app.services.ai_service.get_openai_client", return_value=mock_client):
        request = AIQuizGenerationRequest(
            source_text="테스트 텍스트",
            subject_name="데이터 분석",
        )
        
        with pytest.raises(ValueError, match="AI 응답이 비어있습니다"):
            await generate_quiz(request)
