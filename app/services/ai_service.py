import asyncio
import json
import logging
import os
import random

from google import genai
from google.genai import types
from google.genai.errors import ServerError, ClientError

from app.core.config import settings
from app.exceptions import GeminiServiceUnavailableError, GeminiAPIKeyError
from app.schemas.ai import AIQuizGenerationRequest, AIQuizGenerationResponse

logger = logging.getLogger(__name__)

_gemini_client: genai.Client | None = None
# 동시 Gemini API 요청 수 제한 (과부하 방지)
_gemini_semaphore: asyncio.Semaphore | None = None


def get_gemini_client() -> genai.Client:
    """Gemini 클라이언트 싱글톤"""
    global _gemini_client
    if _gemini_client is None:
        api_key = settings.gemini_api_key or os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY가 설정되지 않았습니다")
        _gemini_client = genai.Client(api_key=api_key)
    return _gemini_client


def get_gemini_semaphore() -> asyncio.Semaphore:
    """Gemini API 동시 요청 제한 Semaphore 싱글톤"""
    global _gemini_semaphore
    if _gemini_semaphore is None:
        # 환경변수에서 동시 요청 수 가져오기 (기본값: 2)
        max_concurrent = int(os.getenv("GEMINI_MAX_CONCURRENT", "2"))
        _gemini_semaphore = asyncio.Semaphore(max_concurrent)
        logger.info(f"Gemini API 동시 요청 제한 설정: 최대 {max_concurrent}개")
    return _gemini_semaphore


async def generate_quiz_with_gemini(request: AIQuizGenerationRequest) -> AIQuizGenerationResponse:
    """Gemini를 사용하여 문제 생성 (무료, 재시도 로직 포함, 동시 요청 제한)"""
    client = get_gemini_client()
    semaphore = get_gemini_semaphore()
    
    # 카테고리 정보 구성
    category_info = request.subject_name
    if request.main_topic_name:
        category_info += f" > {request.main_topic_name}"
    if request.sub_topic_name:
        category_info += f" > {request.sub_topic_name}"
    
    prompt = f"""당신은 교육용 문제 생성 전문가입니다.

카테고리: {category_info}

위 카테고리에서 객관식 문제 1개를 생성하세요.

텍스트: {request.source_text}

**참고**: 위 텍스트는 기존 데이터와 새로 추가된 데이터가 종합된 내용입니다. 모든 정보를 종합하여 정교한 문제를 생성하세요.

다음 JSON 형식으로 응답하세요:
{{
  "question": "문제 내용",
  "options": [
    {{"index": 0, "text": "정답 선택지"}},
    {{"index": 1, "text": "오답 선택지 1"}},
    {{"index": 2, "text": "오답 선택지 2"}},
    {{"index": 3, "text": "오답 선택지 3"}}
  ],
  "correct_answer": 0,
  "explanation": "해설"
}}

요구사항:
- 명확한 문제
- 정답 1개 (index: 0)
- 오답 3개 (index: 1-3, 매력적인 오답으로 구성)
- 정답 인덱스는 항상 0
- 간결한 해설
- 오답들은 정답과 유사하지만 틀린 내용이어야 함
- 반드시 4지선다 형식으로 생성 (총 4개 선택지)
- **중요**: 생성된 문제는 반드시 위 카테고리({category_info})와 직접적으로 관련된 내용이어야 합니다
- **중요**: 문제, 선택지, 해설 모두 카테고리 주제와 일치해야 하며, 다른 카테고리 내용이 포함되어서는 안 됩니다
- **중요**: 제공된 텍스트가 카테고리와 관련이 없으면, 카테고리 주제에 맞는 문제를 생성하되 제공된 텍스트의 핵심 개념을 활용하세요"""

    # 재시도 설정 (503 에러 대응 강화)
    max_retries = 5  # 재시도 횟수 증가 (3회 → 5회)
    base_delay = 2.0  # 초기 대기 시간 증가 (1초 → 2초)
    max_delay = 16.0  # 최대 대기 시간 제한 (16초)
    
    # Semaphore로 동시 요청 수 제한 (과부하 방지)
    async with semaphore:
        logger.debug(f"Gemini API 요청 시작 (동시 요청 제한: 최대 {semaphore._value + 1}개)")
        
        for attempt in range(max_retries):
            try:
                # Gemini는 동기 API이므로 asyncio로 래핑
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None,
                    lambda: client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            temperature=0.7,
                            response_mime_type="application/json",
                        ),
                    )
                )
                
                result = response.text
                if not result:
                    raise ValueError("AI 응답이 비어있습니다")
                
                # JSON 파싱 (마크다운 코드 블록 제거)
                result = result.strip()
                if result.startswith("```json"):
                    result = result[7:]
                if result.startswith("```"):
                    result = result[3:]
                if result.endswith("```"):
                    result = result[:-3]
                result = result.strip()
                
                data = json.loads(result)
                
                # 성공 시 로그 출력 (첫 시도가 아니면)
                if attempt > 0:
                    logger.info(f"Gemini API 호출 성공 (시도 {attempt + 1}/{max_retries})")
                
                # 카테고리 검증 로깅
                quiz_response = AIQuizGenerationResponse(**data)
                logger.info(
                    f"문제 생성 완료 - 카테고리: {category_info}, "
                    f"문제: {quiz_response.question[:50]}..., "
                    f"정답 인덱스: {quiz_response.correct_answer}"
                )
                
                return quiz_response
                
            except ClientError as e:
                # 403 에러 확인 (API 키 문제)
                error_message = str(e).lower()
                if "403" in str(e) or "permission_denied" in error_message or "leaked" in error_message:
                    logger.error(
                        f"Gemini API 키 문제 감지: status_code=403, "
                        f"error_type={type(e).__name__}"
                    )
                    raise GeminiAPIKeyError(
                        "Gemini API 키 문제로 문제 생성에 실패했습니다. 관리자에게 문의하세요."
                    )
                else:
                    # 403이 아닌 다른 ClientError는 그대로 전파
                    logger.error(
                        f"Gemini API ClientError: status_code={getattr(e, 'status_code', 'unknown')}, "
                        f"error_type={type(e).__name__}"
                    )
                    raise
            except ServerError as e:
                # 503 에러 확인
                error_message = str(e)
                if "503" in error_message or "UNAVAILABLE" in error_message or "overloaded" in error_message.lower():
                    if attempt < max_retries - 1:
                        # 지수 백오프 + jitter: 2초, 4초, 8초, 16초 (최대 16초)
                        exponential_delay = base_delay * (2 ** attempt)
                        delay = min(exponential_delay, max_delay)
                        # Jitter 추가: ±20% 랜덤 변동으로 동시 요청 분산
                        jitter = delay * 0.2 * (random.random() * 2 - 1)  # -20% ~ +20%
                        delay_with_jitter = max(0.5, delay + jitter)  # 최소 0.5초 보장
                        
                        logger.warning(
                            f"Gemini API 503 에러 발생 (시도 {attempt + 1}/{max_retries}). "
                            f"{delay_with_jitter:.1f}초 후 재시도합니다. (에러: {error_message[:100]})"
                        )
                        await asyncio.sleep(delay_with_jitter)
                        continue
                    else:
                        # 최대 재시도 횟수 도달
                        logger.error(
                            f"Gemini API 503 에러: 최대 재시도 횟수({max_retries}) 도달. "
                            f"총 {max_retries}회 시도 후 실패. 에러 메시지: {error_message}"
                        )
                        raise GeminiServiceUnavailableError(
                            "Gemini API가 일시적으로 과부하 상태입니다. 잠시 후 다시 시도해주세요."
                        )
                else:
                    # 503이 아닌 다른 ServerError는 그대로 전파
                    logger.error(f"Gemini API ServerError (503 아님): {error_message}")
                    raise
            except Exception as e:
                # 다른 예외는 재시도하지 않고 즉시 전파
                logger.error(
                    f"Gemini API 호출 중 예외 발생: error_type={type(e).__name__}, "
                    f"error_message={str(e)[:200]}"
                )
                raise


async def generate_quiz(request: AIQuizGenerationRequest) -> AIQuizGenerationResponse:
    """AI를 사용하여 문제 생성 (Gemini 사용)"""
    if not settings.gemini_api_key:
        raise ValueError("GEMINI_API_KEY가 설정되지 않았습니다")
    return await generate_quiz_with_gemini(request)


async def validate_quiz_with_gemini(
    question: str,
    options: list[dict],
    explanation: str,
    category: str,
) -> dict:
    """Gemini를 사용하여 문제가 카테고리에 맞는지 검증"""
    client = get_gemini_client()
    semaphore = get_gemini_semaphore()
    
    options_text = "\n".join([f"{opt['index']}. {opt['text']}" for opt in options])
    
    prompt = f"""당신은 교육용 문제 검증 전문가입니다.

카테고리: {category}

다음 문제가 위 카테고리와 일치하는지 검증하세요.

문제: {question}
선택지:
{options_text}
해설: {explanation}

다음 JSON 형식으로 응답하세요:
{{
  "is_valid": true,
  "validation_score": 0.95,
  "feedback": "검증 피드백",
  "issues": ["발견된 문제점 1", "발견된 문제점 2"]
}}

**중요: 점수 계산 기준**
- validation_score는 0.0-1.0 사이의 점수입니다
- 점수는 카테고리 일치도, 문제 품질, 선택지 적합성, 해설 명확성을 종합적으로 평가합니다
- **점수 범위별 의미:**
  * 0.9-1.0: 매우 우수 (카테고리 완벽 일치, 문제 품질 매우 높음)
  * 0.8-0.89: 우수 (카테고리 일치, 문제 품질 높음)
  * 0.7-0.79: 양호 (카테고리 일치, 일부 개선 여지 있음)
  * 0.6-0.69: 보통 (카테고리 대체로 일치, 개선 필요)
  * 0.5-0.59: 미흡 (카테고리와 부분 일치, 수정 권장)
  * 0.0-0.49: 부적합 (카테고리 불일치 또는 심각한 문제)

**is_valid와 validation_score의 관계:**
- is_valid=true인 경우: validation_score는 반드시 0.7 이상이어야 합니다
- is_valid=false인 경우: validation_score는 0.7 미만입니다
- **일관성 필수**: is_valid와 validation_score는 반드시 일치해야 합니다

요구사항:
- is_valid: 카테고리와 일치하고 문제 품질이 양호하면 true, 아니면 false
- validation_score: 위 기준에 따라 정확히 계산 (0.0-1.0)
- feedback: 검증 결과에 대한 상세 피드백 (점수 근거 포함)
- issues: 발견된 문제점 리스트 (없으면 빈 배열)

**예시:**
- 문제가 카테고리와 완벽히 일치하고 품질이 우수한 경우: {{"is_valid": true, "validation_score": 0.95}}
- 문제가 카테고리와 일치하지만 일부 개선이 필요한 경우: {{"is_valid": true, "validation_score": 0.75}}
- 문제가 카테고리와 불일치하거나 심각한 문제가 있는 경우: {{"is_valid": false, "validation_score": 0.3}}"""

    async with semaphore:
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.3,
                        response_mime_type="application/json",
                    ),
                )
            )
            
            result = response.text.strip()
            if result.startswith("```json"):
                result = result[7:]
            if result.startswith("```"):
                result = result[3:]
            if result.endswith("```"):
                result = result[:-3]
            result = result.strip()
            
            data = json.loads(result)
            logger.info(f"문제 검증 완료: is_valid={data.get('is_valid')}, score={data.get('validation_score')}")
            return data
            
        except Exception as e:
            logger.error(f"문제 검증 중 오류: {e.__class__.__name__}: {str(e)}")
            raise


async def evaluate_correction_request_with_gemini(
    quiz_question: str,
    quiz_options: list[dict],
    quiz_explanation: str,
    category: str,
    correction_request: str,
    suggested_correction: str | None = None,
) -> dict:
    """Gemini를 사용하여 수정 요청이 타당한지 평가하고 수정된 문제 생성"""
    client = get_gemini_client()
    semaphore = get_gemini_semaphore()
    
    options_text = "\n".join([f"{opt['index']}. {opt['text']}" for opt in quiz_options])
    suggested_text = f"\n제안된 수정 내용: {suggested_correction}" if suggested_correction else ""
    
    prompt = f"""당신은 교육용 문제 수정 전문가입니다.

카테고리: {category}

원본 문제:
문제: {quiz_question}
선택지:
{options_text}
해설: {quiz_explanation}

수정 요청: {correction_request}
{suggested_text}

다음 JSON 형식으로 응답하세요:
{{
  "is_valid_request": true,
  "validation_feedback": "수정 요청이 타당한지에 대한 평가",
  "corrected_question": "수정된 문제 내용",
  "corrected_options": [
    {{"index": 0, "text": "수정된 정답 선택지"}},
    {{"index": 1, "text": "수정된 오답 선택지 1"}},
    {{"index": 2, "text": "수정된 오답 선택지 2"}},
    {{"index": 3, "text": "수정된 오답 선택지 3"}}
  ],
  "correct_answer": 0,
  "corrected_explanation": "수정된 해설"
}}

요구사항:
- is_valid_request: 수정 요청이 타당하면 true, 아니면 false
- validation_feedback: 수정 요청에 대한 평가 (타당한 경우 왜 타당한지, 타당하지 않은 경우 왜 타당하지 않은지)
- 수정 요청이 타당한 경우에만 corrected_* 필드를 채우세요
- 수정 요청이 타당하지 않은 경우 corrected_* 필드는 null로 설정하세요
- 수정된 문제는 반드시 카테고리({category})와 일치해야 합니다
- 4지선다 형식을 유지하세요"""

    async with semaphore:
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.7,
                        response_mime_type="application/json",
                    ),
                )
            )
            
            result = response.text.strip()
            if result.startswith("```json"):
                result = result[7:]
            if result.startswith("```"):
                result = result[3:]
            if result.endswith("```"):
                result = result[:-3]
            result = result.strip()
            
            data = json.loads(result)
            logger.info(f"수정 요청 평가 완료: is_valid_request={data.get('is_valid_request')}")
            return data
            
        except Exception as e:
            logger.error(f"수정 요청 평가 중 오류: {e.__class__.__name__}: {str(e)}")
            raise
