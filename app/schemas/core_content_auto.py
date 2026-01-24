from datetime import datetime

from pydantic import BaseModel, Field


class CoreContentAutoRequest(BaseModel):
    """핵심 정보 자동 분류 요청 스키마"""
    core_content: str = Field(..., description="핵심 정보 텍스트 (URL 또는 텍스트)")
    source_type: str = Field(..., description="소스 타입 (text | youtube_url)")


class CoreContentAutoCandidateResponse(BaseModel):
    """자동 분류 후보 응답 스키마"""
    sub_topic_id: int
    category_path: str
    score: float
    rank: int


class CoreContentAutoResponse(BaseModel):
    """핵심 정보 자동 분류 응답 스키마"""
    id: int
    category_path: str | None = Field(default=None, description="자동 분류된 카테고리 경로")
    confidence: float | None = Field(default=None, description="자동 분류 확신 점수")
    candidates: list[CoreContentAutoCandidateResponse] = Field(default_factory=list)
    updated_at: datetime | None = None


class CoreContentAutoSettingsResponse(BaseModel):
    """자동 분류 설정 응답"""
    min_confidence: float
    strategy: str
    keyword_weight: float
    similarity_weight: float
    max_candidates: int
    text_preview_length: int

    model_config = {"from_attributes": True}


class CoreContentCategoryRuleRequest(BaseModel):
    """카테고리 가중치/우선순위 규칙 요청"""
    sub_topic_id: int
    weight: float = Field(1.0, ge=0)
    priority: int = Field(0, ge=0)
    is_active: bool = True


class CoreContentAutoSettingsUpdateRequest(BaseModel):
    """자동 분류 설정 업데이트 요청"""
    min_confidence: float | None = Field(None, ge=0, le=1)
    strategy: str | None = None
    keyword_weight: float | None = Field(None, ge=0)
    similarity_weight: float | None = Field(None, ge=0)
    max_candidates: int | None = Field(None, ge=1, le=10)
    text_preview_length: int | None = Field(None, ge=50, le=2000)
    category_rules: list[CoreContentCategoryRuleRequest] | None = None


class CoreContentAutoPendingItem(BaseModel):
    """자동 분류 보류 항목"""
    run_id: int
    request_core_content: str
    source_type: str
    classification_text_preview: str
    auto_sub_topic_id: int | None
    auto_confidence: float | None
    status: str
    created_at: datetime
    candidates: list[CoreContentAutoCandidateResponse] = Field(default_factory=list)


class CoreContentAutoPendingResponse(BaseModel):
    """자동 분류 보류 목록 응답"""
    items: list[CoreContentAutoPendingItem]
    total: int
    page: int
    limit: int


class CoreContentAutoReviewRequest(BaseModel):
    """자동 분류 승인 요청"""
    sub_topic_id: int
    reason: str | None = None


class CoreContentAutoRejectRequest(BaseModel):
    """자동 분류 거절 요청"""
    reason: str | None = None


class CoreContentAutoReviewResponse(BaseModel):
    """자동 분류 검수 응답"""
    run_id: int
    status: str
    final_sub_topic_id: int | None
    updated_at: datetime
