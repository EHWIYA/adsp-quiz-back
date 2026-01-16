from openai import AsyncOpenAI

from app.core.config import settings
from app.schemas.ai import AIQuizGenerationRequest, AIQuizGenerationResponse


_client: AsyncOpenAI | None = None


def get_openai_client() -> AsyncOpenAI:
    """OpenAI 클라이언트 싱글톤"""
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=settings.openai_api_key)
    return _client


async def generate_quiz(request: AIQuizGenerationRequest) -> AIQuizGenerationResponse:
    """AI를 사용하여 문제 생성 (Structured Output)"""
    client = get_openai_client()
    
    prompt = f"""다음 텍스트를 기반으로 {request.subject_name} 과목의 객관식 문제 1개를 생성하세요.

텍스트:
{request.source_text}

요구사항:
- 문제는 명확하고 구체적이어야 함
- 선택지 4개 (인덱스 0-3)
- 정답은 인덱스로 표시 (0-3)
- 해설은 간결하고 명확하게"""

    response = await client.beta.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "당신은 교육용 문제 생성 전문가입니다."},
            {"role": "user", "content": prompt},
        ],
        response_format={"type": "json_schema", "json_schema": {
            "name": "quiz_generation",
            "strict": True,
            "schema": {
                "type": "object",
                "properties": {
                    "question": {"type": "string"},
                    "options": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "index": {"type": "integer", "minimum": 0, "maximum": 3},
                                "text": {"type": "string"},
                            },
                            "required": ["index", "text"],
                        },
                        "minItems": 4,
                        "maxItems": 4,
                    },
                    "correct_answer": {"type": "integer", "minimum": 0, "maximum": 3},
                    "explanation": {"type": "string"},
                },
                "required": ["question", "options", "correct_answer", "explanation"],
            },
        }},
        temperature=0.7,
    )

    result = response.choices[0].message.content
    if not result:
        raise ValueError("AI 응답이 비어있습니다")
    
    import json
    data = json.loads(result)
    return AIQuizGenerationResponse(**data)
