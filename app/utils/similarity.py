"""유사도 계산 유틸리티 (토큰 없이, 한국어 특성 고려)"""
import re


# 한국어 조사/어미 패턴
KOREAN_PARTICLES = {
    "의", "는", "은", "이", "가", "을", "를", "에", "에서", "와", "과", 
    "도", "만", "부터", "까지", "로", "으로", "처럼", "같이", "보다",
    "한테", "에게", "께", "더러", "에게서", "한테서"
}

# 유사 표현 매핑
SIMILAR_EXPRESSIONS = {
    "무엇인가": "무엇",
    "무엇인가요": "무엇",
    "무엇인지": "무엇",
    "무엇인": "무엇",
    "어떤": "어떤",
    "어떤가": "어떤",
    "어떤지": "어떤",
    "어떤": "어떤",
}


def normalize_korean_text(text: str) -> str:
    """한국어 텍스트 정규화
    
    - 구두점 제거
    - 조사/어미 제거
    - 유사 표현 정규화
    - 공백 정규화
    """
    if not text:
        return ""
    
    # 구두점 제거
    text = re.sub(r'[?!.,;:()\[\]{}"\']+', '', text)
    
    # 공백 정규화
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text


def extract_normalized_words(text: str) -> set[str]:
    """정규화된 단어 추출
    
    조사/어미를 제거하고 유사 표현을 정규화하여 단어 집합 반환
    """
    normalized = normalize_korean_text(text)
    if not normalized:
        return set()
    
    words = normalized.split()
    normalized_words = set()
    
    for word in words:
        # 조사 제거 (단어 끝에 붙은 조사)
        cleaned = word
        for particle in KOREAN_PARTICLES:
            if cleaned.endswith(particle):
                cleaned = cleaned[:-len(particle)]
                break
        
        # 유사 표현 정규화
        if cleaned in SIMILAR_EXPRESSIONS:
            cleaned = SIMILAR_EXPRESSIONS[cleaned]
        
        # 빈 문자열이 아니고 길이가 1 이상인 경우만 추가
        if cleaned and len(cleaned) >= 1:
            normalized_words.add(cleaned)
    
    return normalized_words


def get_character_ngrams(text: str, n: int = 2) -> set[str]:
    """문자 n-gram 추출"""
    if len(text) < n:
        return set()
    
    ngrams = set()
    for i in range(len(text) - n + 1):
        ngram = text[i:i+n]
        ngrams.add(ngram)
    
    return ngrams


def calculate_jaccard_similarity(set1: set[str], set2: set[str]) -> float:
    """Jaccard 유사도 계산"""
    if not set1 or not set2:
        return 0.0
    
    intersection = set1 & set2
    union = set1 | set2
    
    return len(intersection) / len(union) if union else 0.0


def calculate_question_similarity(q1: str, q2: str) -> float:
    """문제 텍스트 유사도 계산 (토큰 없이, 정교한 방식)
    
    다중 유사도 지표를 조합하여 정확도를 향상:
    1. 정규화된 단어 Jaccard 유사도 (가중치: 0.6)
    2. 문자 2-gram 유사도 (가중치: 0.3)
    3. 문자 3-gram 유사도 (가중치: 0.1)
    
    Args:
        q1: 첫 번째 문제 텍스트
        q2: 두 번째 문제 텍스트
    
    Returns:
        0.0 ~ 1.0 사이의 유사도 (1.0이 완전 동일)
    """
    if not q1 or not q2:
        return 0.0
    
    # 1. 정규화된 단어 Jaccard 유사도 (가중치: 0.6)
    words1 = extract_normalized_words(q1)
    words2 = extract_normalized_words(q2)
    word_similarity = calculate_jaccard_similarity(words1, words2)
    
    # 2. 문자 2-gram 유사도 (가중치: 0.3)
    normalized_q1 = normalize_korean_text(q1)
    normalized_q2 = normalize_korean_text(q2)
    bigrams1 = get_character_ngrams(normalized_q1, n=2)
    bigrams2 = get_character_ngrams(normalized_q2, n=2)
    bigram_similarity = calculate_jaccard_similarity(bigrams1, bigrams2)
    
    # 3. 문자 3-gram 유사도 (가중치: 0.1)
    trigrams1 = get_character_ngrams(normalized_q1, n=3)
    trigrams2 = get_character_ngrams(normalized_q2, n=3)
    trigram_similarity = calculate_jaccard_similarity(trigrams1, trigrams2)
    
    # 가중 평균
    final_similarity = (
        word_similarity * 0.6 +
        bigram_similarity * 0.3 +
        trigram_similarity * 0.1
    )
    
    return round(final_similarity, 4)
