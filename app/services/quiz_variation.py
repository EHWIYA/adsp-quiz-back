"""문제 변형 서비스 (기존 문제 재사용 시 완전 동일 방지)"""
import json
import logging
import random

from app.schemas.ai import AIQuizGenerationResponse
from app.schemas.quiz import QuizOptionResponse, QuizResponse

logger = logging.getLogger(__name__)


def vary_quiz_options(quiz: QuizResponse) -> QuizResponse:
    """문제의 선택지 변형 (오답 풀 활용 또는 순서 섞기)"""
    options = quiz.options.copy()
    correct_option = options[quiz.correct_answer]
    
    # 오답 선택지 추출
    wrong_options = [opt for i, opt in enumerate(options) if i != quiz.correct_answer]
    
    # 오답 풀이 3개 이상이면 랜덤으로 3개 선택 (다양성 보장)
    if len(wrong_options) >= 3:
        selected_wrong_options = random.sample(wrong_options, 3)
        # 정답 1개 + 오답 3개 = 4개 구성
        new_options = [correct_option] + selected_wrong_options
        random.shuffle(new_options)  # 순서 섞기
        
        # 새로운 정답 인덱스 찾기
        new_correct_answer = next(
            i for i, opt in enumerate(new_options) if opt.text == correct_option.text
        )
        
        logger.debug(
            f"오답 풀 활용: quiz_id={quiz.id}, "
            f"오답 풀 {len(wrong_options)}개 중 3개 선택, "
            f"정답 인덱스 {quiz.correct_answer} → {new_correct_answer}"
        )
    else:
        # 오답 풀이 3개 미만이면 기존 방식 (순서만 섞기)
        random.shuffle(options)
        new_options = options
        new_correct_answer = next(
            i for i, opt in enumerate(new_options) if opt.text == correct_option.text
        )
        
        logger.debug(
            f"선택지 순서 섞기: quiz_id={quiz.id}, "
            f"정답 인덱스 {quiz.correct_answer} → {new_correct_answer}"
        )
    
    # 변형된 문제 반환
    varied_quiz = QuizResponse(
        id=quiz.id,
        subject_id=quiz.subject_id,
        question=quiz.question,
        options=new_options,
        correct_answer=new_correct_answer,
        explanation=quiz.explanation,
        source_url=quiz.source_url,
        created_at=quiz.created_at,
    )
    
    return varied_quiz


def vary_quiz_question(quiz: QuizResponse) -> QuizResponse:
    """문제 문장을 약간 변형 (의미 있는 변형만)"""
    question = quiz.question
    options = quiz.options.copy()
    correct_answer = quiz.correct_answer
    
    # 변형 패턴 (원본 제외)
    variations = []
    
    # 1. "에 대한 설명으로 옳은 것은?" 접미사 추가
    if not question.endswith("에 대한 설명으로 옳은 것은?"):
        base_question = question.replace("?", "").strip()
        variations.append({
            "question": f"{base_question}에 대한 설명으로 옳은 것은?",
            "options": options,
            "correct_answer": correct_answer,
        })
    
    # 2. "옳은 것" → "옳지 않은 것" 변형 (오답 풀 활용)
    if "옳은 것" in question or "올바른 것" in question or "맞는 것" in question:
        # 문제 문장 변형
        varied_question = question.replace("옳은 것", "옳지 않은 것")
        varied_question = varied_question.replace("올바른 것", "올바르지 않은 것")
        varied_question = varied_question.replace("맞는 것", "맞지 않은 것")
        
        # 오답 풀에서 1개를 정답으로 승격, 기존 정답은 오답으로
        original_correct_option = options[correct_answer]
        wrong_options = [opt for i, opt in enumerate(options) if i != correct_answer]
        
        # 오답 풀이 3개 이상이면 랜덤으로 1개를 정답으로, 나머지 2개 + 기존 정답 = 3개 오답
        if len(wrong_options) >= 3:
            # 오답 풀에서 1개를 정답으로 승격
            new_correct_option = random.choice(wrong_options)
            # 나머지 오답 2개 + 기존 정답 = 3개 오답
            remaining_wrong = [opt for opt in wrong_options if opt.text != new_correct_option.text]
            selected_wrong = random.sample(remaining_wrong, min(2, len(remaining_wrong)))
            new_wrong_options = selected_wrong + [original_correct_option]
            random.shuffle(new_wrong_options)
            
            # 정답 1개 + 오답 3개 = 4개 구성
            new_options = [new_correct_option] + new_wrong_options
            new_correct_answer = 0  # 정답은 항상 첫 번째
            
            logger.debug(
                f"역전 로직 (오답 풀 활용): quiz_id={quiz.id}, "
                f"오답 풀 {len(wrong_options)}개 중 1개를 정답으로 승격"
            )
        else:
            # 오답 풀이 부족하면 기존 방식 (순서만 섞기)
            shuffled_options = options.copy()
            random.shuffle(shuffled_options)
            new_options = shuffled_options
            new_correct_answer = next(
                i for i, opt in enumerate(new_options) 
                if opt.text == original_correct_option.text
            )
        
        variations.append({
            "question": varied_question,
            "options": new_options,
            "correct_answer": new_correct_answer,
        })
    
    # 변형이 없으면 원본 반환
    if not variations:
        return quiz
    
    # 원본과 다른 변형 선택
    variation = random.choice(variations)
    
    varied_quiz = QuizResponse(
        id=quiz.id,
        subject_id=quiz.subject_id,
        question=variation["question"],
        options=variation["options"],
        correct_answer=variation["correct_answer"],
        explanation=quiz.explanation,
        source_url=quiz.source_url,
        created_at=quiz.created_at,
    )
    
    logger.debug(f"문제 문장 변형: quiz_id={quiz.id}")
    
    return varied_quiz


def vary_quiz(quiz: QuizResponse, variation_type: str | None = None) -> QuizResponse:
    """문제 변형 (선택지 순서 섞기 또는 문제 문장 변형)"""
    if variation_type is None:
        # 랜덤으로 변형 타입 선택
        variation_type = random.choice(["options", "question", "both"])
    
    if variation_type == "options":
        return vary_quiz_options(quiz)
    elif variation_type == "question":
        return vary_quiz_question(quiz)
    elif variation_type == "both":
        # 두 가지 모두 적용
        varied = vary_quiz_options(quiz)
        return vary_quiz_question(varied)
    else:
        # 변형 없이 반환
        return quiz
