import json
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class WrongAnswerCreateRequest(BaseModel):
    quiz_id: int = Field(..., description="문제 ID")
    question: str = Field(..., description="문제 내용")
    options: list[str] = Field(..., description="선택지 목록")
    selected_answer: int = Field(..., ge=0, description="선택한 답안 인덱스")
    correct_answer: int = Field(..., ge=0, description="정답 인덱스")
    explanation: str | None = Field(None, description="해설")
    subject_id: int | None = Field(None, description="과목 ID")
    sub_topic_id: int | None = Field(None, description="세부항목 ID")
    created_at: str | None = Field(None, description="원본 문제의 created_at (ISO 8601 형식)")


class WrongAnswerResponse(BaseModel):
    id: int
    quiz_id: int
    question: str
    options: list[str]
    selected_answer: int
    correct_answer: int
    explanation: str | None
    subject_id: int | None
    sub_topic_id: int | None
    created_at: str
    saved_at: str
    updated_at: str | None = None

    @model_validator(mode="before")
    @classmethod
    def parse_options(cls, data):
        if not isinstance(data, dict):
            data = {
                "id": getattr(data, "id", None),
                "quiz_id": getattr(data, "quiz_id", None),
                "question": getattr(data, "question", None),
                "options": getattr(data, "options", None),
                "selected_answer": getattr(data, "selected_answer", None),
                "correct_answer": getattr(data, "correct_answer", None),
                "explanation": getattr(data, "explanation", None),
                "subject_id": getattr(data, "subject_id", None),
                "sub_topic_id": getattr(data, "sub_topic_id", None),
                "created_at": getattr(data, "created_at_original", None) or getattr(data, "created_at", None),
                "saved_at": getattr(data, "saved_at", None),
                "updated_at": getattr(data, "updated_at", None),
            }
        
        if isinstance(data, dict) and "options" in data:
            options_str = data.get("options")
            if isinstance(options_str, str):
                try:
                    options_list = json.loads(options_str)
                    data["options"] = [opt.get("text", opt) if isinstance(opt, dict) else opt for opt in options_list]
                except (json.JSONDecodeError, TypeError):
                    data["options"] = []
        
        if isinstance(data, dict):
            if "created_at" in data and data["created_at"]:
                if isinstance(data["created_at"], datetime):
                    data["created_at"] = data["created_at"].isoformat()
            elif "created_at" not in data or data.get("created_at") is None:
                saved_at = data.get("saved_at")
                if saved_at:
                    if isinstance(saved_at, datetime):
                        data["created_at"] = saved_at.isoformat()
                    else:
                        data["created_at"] = saved_at
                else:
                    data["created_at"] = ""
            
            if "saved_at" in data and data["saved_at"]:
                if isinstance(data["saved_at"], datetime):
                    data["saved_at"] = data["saved_at"].isoformat()
            
            if "updated_at" in data and data["updated_at"]:
                if isinstance(data["updated_at"], datetime):
                    data["updated_at"] = data["updated_at"].isoformat()
        
        return data

    model_config = {"from_attributes": True}


class WrongAnswerListResponse(BaseModel):
    wrong_answers: list[WrongAnswerResponse]
    total: int
    page: int
    limit: int
    total_pages: int


class WrongAnswerDeleteResponse(BaseModel):
    message: str
    id: int


class WrongAnswerBatchDeleteRequest(BaseModel):
    ids: list[int] = Field(..., description="삭제할 오답노트 ID 목록")


class WrongAnswerBatchDeleteResponse(BaseModel):
    message: str
    deleted_count: int


class WrongAnswerStatsResponse(BaseModel):
    total_count: int
    by_subject: dict[str, int]
    by_sub_topic: dict[str, int]
    recent_count: int = Field(..., description="최근 7일 내 저장된 항목 수")
