import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import quiz as quiz_crud, sub_topic as sub_topic_crud
from app.exceptions import GeminiServiceUnavailableError
from app.models.base import get_db
from app.schemas import ai, quiz as quiz_schema
from app.services import ai_service, youtube_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/quiz", tags=["quiz"])


@router.get("/subjects", response_model=quiz_schema.SubjectListResponse)
async def get_subjects(
    db: AsyncSession = Depends(get_db),
):
    """과목 목록 조회 API"""
    subjects = await quiz_crud.get_all_subjects(db)
    subject_responses = [quiz_schema.SubjectResponse.model_validate(s) for s in subjects]
    return quiz_schema.SubjectListResponse(subjects=subject_responses, total=len(subject_responses))


@router.post("/generate", response_model=quiz_schema.QuizResponse, status_code=status.HTTP_201_CREATED)
async def generate_quiz(
    request: quiz_schema.QuizCreateRequest,
    db: AsyncSession = Depends(get_db),
):
    """문제 생성 API (프론트엔드 호환: camelCase 필드명 지원, subject_id 선택 필드)"""
    # subject_id가 None이면 기본 과목(id=1, ADsP) 사용
    subject_id = request.subject_id or 1
    subject = await quiz_crud.get_subject_by_id(db, subject_id)
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"과목을 찾을 수 없습니다: {subject_id}",
        )

    source_text = None
    source_url = None

    if request.source_type == "url":
        if not request.source_url:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="source_type이 'url'일 때 source_url은 필수입니다",
            )
        video_id = youtube_service.extract_video_id(request.source_url)
        source_text = await youtube_service.extract_transcript(video_id)
        source_url = request.source_url
    else:
        if not request.source_text:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="source_type이 'text'일 때 source_text는 필수입니다",
            )
        source_text = request.source_text

    source_hash = youtube_service.generate_hash(source_text)

    existing_quiz = await quiz_crud.get_quiz_by_hash(db, source_hash)
    if existing_quiz:
        return quiz_schema.QuizResponse.model_validate(existing_quiz)

    ai_request = ai.AIQuizGenerationRequest(
        source_text=source_text,
        subject_name=subject.name,
    )
    
    try:
        ai_response = await ai_service.generate_quiz(ai_request)
    except GeminiServiceUnavailableError as e:
        # Gemini API 일시적 과부하 에러는 503으로 반환
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        )

    new_quiz = await quiz_crud.create_quiz(
        db,
        subject_id=subject_id,
        ai_response=ai_response,
        source_hash=source_hash,
        source_url=source_url,
        source_text=request.source_text if request.source_type == "text" else None,
    )

    return quiz_schema.QuizResponse.model_validate(new_quiz)


@router.get("/{quiz_id}", response_model=quiz_schema.QuizResponse)
async def get_quiz(
    quiz_id: int,
    db: AsyncSession = Depends(get_db),
):
    """문제 조회 API"""
    quiz = await quiz_crud.get_quiz_by_id(db, quiz_id)
    if not quiz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"문제를 찾을 수 없습니다: {quiz_id}",
        )

    return quiz_schema.QuizResponse.model_validate(quiz)


@router.post("/generate-study", response_model=quiz_schema.StudyModeQuizListResponse, status_code=status.HTTP_201_CREATED)
async def generate_study_quizzes(
    request: quiz_schema.StudyModeQuizCreateRequest,
    db: AsyncSession = Depends(get_db),
):
    """학습 모드 문제 생성 API (10개 일괄 생성, 캐싱 지원)"""
    # 세부항목 존재 확인
    sub_topic = await sub_topic_crud.get_sub_topic_with_core_content(db, request.sub_topic_id)
    if not sub_topic:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"세부항목을 찾을 수 없습니다: {request.sub_topic_id}",
        )
    
    # 핵심 정보 확인
    if not sub_topic.core_content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"세부항목에 핵심 정보가 없습니다: {request.sub_topic_id}",
        )
    
    # 캐시된 문제 조회
    cached_quizzes = await quiz_crud.get_quizzes_by_sub_topic_id(
        db,
        request.sub_topic_id,
        request.quiz_count
    )
    
    # 캐시된 문제가 충분한 경우
    if len(cached_quizzes) >= request.quiz_count:
        logger.info(
            f"캐시된 문제 사용: sub_topic_id={request.sub_topic_id}, "
            f"요청={request.quiz_count}, 캐시={len(cached_quizzes)}"
        )
        quiz_responses = [
            quiz_schema.QuizResponse.model_validate(q) for q in cached_quizzes[:request.quiz_count]
        ]
        return quiz_schema.StudyModeQuizListResponse(
            quizzes=quiz_responses,
            total_count=len(quiz_responses)
        )
    
    # 부족한 문제 개수 계산
    needed_count = request.quiz_count - len(cached_quizzes)
    logger.info(
        f"새 문제 생성 필요: sub_topic_id={request.sub_topic_id}, "
        f"요청={request.quiz_count}, 캐시={len(cached_quizzes)}, 생성={needed_count}"
    )
    
    # 새 문제 생성
    new_quizzes = []
    subject_id = sub_topic.main_topic.subject_id
    
    for i in range(needed_count):
        try:
            # 핵심 정보를 기반으로 문제 생성
            ai_request = ai.AIQuizGenerationRequest(
                source_text=sub_topic.core_content,
                subject_name=sub_topic.main_topic.subject.name,
            )
            
            ai_response = await ai_service.generate_quiz(ai_request)
            
            # 해시 생성 (핵심 정보 + 인덱스로 고유성 보장)
            source_hash = youtube_service.generate_hash(
                f"{sub_topic.core_content}_{request.sub_topic_id}_{i}"
            )
            
            # 중복 확인
            existing_quiz = await quiz_crud.get_quiz_by_hash(db, source_hash)
            if existing_quiz:
                # 이미 존재하는 문제는 캐시에 추가
                if existing_quiz.sub_topic_id != request.sub_topic_id:
                    # 다른 세부항목의 문제인 경우 sub_topic_id 업데이트
                    existing_quiz.sub_topic_id = request.sub_topic_id
                    await db.commit()
                    await db.refresh(existing_quiz)
                new_quizzes.append(existing_quiz)
                continue
            
            # 새 문제 생성
            new_quiz = await quiz_crud.create_quiz(
                db,
                subject_id=subject_id,
                ai_response=ai_response,
                source_hash=source_hash,
                source_url=None,
                source_text=sub_topic.core_content,
                sub_topic_id=request.sub_topic_id,
            )
            new_quizzes.append(new_quiz)
            
        except GeminiServiceUnavailableError as e:
            logger.error(
                f"Gemini API 과부하: sub_topic_id={request.sub_topic_id}, "
                f"생성 중단 (생성된 문제: {len(new_quizzes)}/{needed_count})"
            )
            # 일부 문제라도 생성되었으면 반환
            if new_quizzes or cached_quizzes:
                break
            # 문제가 하나도 없으면 에러 반환
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=str(e),
            )
        except Exception as e:
            logger.error(
                f"문제 생성 중 오류: sub_topic_id={request.sub_topic_id}, "
                f"에러={e.__class__.__name__}: {str(e)}",
                exc_info=True
            )
            # 일부 문제라도 생성되었으면 반환
            if new_quizzes or cached_quizzes:
                break
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"문제 생성 중 오류가 발생했습니다: {str(e)}",
            )
    
    # 캐시된 문제 + 새로 생성한 문제 합치기
    all_quizzes = list(cached_quizzes) + new_quizzes
    
    # 요청한 개수만큼만 반환
    quiz_responses = [
        quiz_schema.QuizResponse.model_validate(q) for q in all_quizzes[:request.quiz_count]
    ]
    
    logger.info(
        f"학습 모드 문제 생성 완료: sub_topic_id={request.sub_topic_id}, "
        f"요청={request.quiz_count}, 반환={len(quiz_responses)} "
        f"(캐시={len(cached_quizzes)}, 신규={len(new_quizzes)})"
    )
    
    return quiz_schema.StudyModeQuizListResponse(
        quizzes=quiz_responses,
        total_count=len(quiz_responses)
    )
