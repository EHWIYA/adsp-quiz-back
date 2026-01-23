from datetime import datetime

from pydantic import BaseModel, Field


class SubTopicResponse(BaseModel):
    """세부항목 응답 스키마"""
    id: int
    name: str
    description: str | None
    main_topic_id: int
    created_at: datetime

    model_config = {"from_attributes": True}


class SubTopicListResponse(BaseModel):
    """세부항목 목록 응답 스키마"""
    sub_topics: list[SubTopicResponse]
    total: int


class SubTopicCoreContentUpdateRequest(BaseModel):
    """세부항목 핵심 정보 업데이트 요청 스키마"""
    core_content: str = Field(..., description="핵심 정보 텍스트 (URL 또는 텍스트)")
    source_type: str = Field(..., description="소스 타입 (text | youtube_url)")


class CoreContentItem(BaseModel):
    """핵심 정보 항목 스키마"""
    index: int = Field(..., description="핵심 정보 인덱스 (순서)")
    core_content: str = Field(..., description="핵심 정보 텍스트")
    source_type: str = Field(..., description="소스 타입 (text | youtube_url)")


class SubTopicCoreContentResponse(BaseModel):
    """세부항목 핵심 정보 응답 스키마 (목록 형식)"""
    id: int
    name: str
    core_contents: list[CoreContentItem] = Field(default_factory=list, description="핵심 정보 목록")
    updated_at: datetime

    model_config = {"from_attributes": True}
