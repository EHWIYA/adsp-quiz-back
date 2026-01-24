"""Core Content API 통합 테스트"""
import pytest
from sqlalchemy import select

from app.models.core_content_auto import (
    CoreContentAutoOverride,
    CoreContentAutoRun,
    CoreContentAutoSetting,
)
from app.models.subject import Subject
from app.models.main_topic import MainTopic
from app.models.sub_topic import SubTopic
from app.services import youtube_service


@pytest.mark.asyncio
async def test_get_core_content(client, test_db_session):
    """세부항목 핵심 정보 조회 (목록 형식)"""
    subject = Subject(id=1, name="ADsP", description="테스트 과목")
    main_topic = MainTopic(id=1, subject_id=1, name="주요항목1", description="테스트 주요항목")
    sub_topic = SubTopic(
        id=1,
        main_topic_id=1,
        name="세부항목1",
        description="테스트 세부항목",
        core_content="핵심 정보 내용",
        source_type="text"
    )
    test_db_session.add(subject)
    test_db_session.add(main_topic)
    test_db_session.add(sub_topic)
    await test_db_session.commit()
    
    response = client.get("/api/v1/core-content/1")
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["name"] == "세부항목1"
    assert "core_contents" in data
    assert isinstance(data["core_contents"], list)
    assert len(data["core_contents"]) == 1
    assert data["core_contents"][0]["core_content"] == "핵심 정보 내용"
    assert data["core_contents"][0]["source_type"] == "text"
    assert "updated_at" in data


@pytest.mark.asyncio
async def test_get_core_content_not_found(client, test_db_session):
    """세부항목 핵심 정보 조회 (존재하지 않는 ID)"""
    response = client.get("/api/v1/core-content/999")
    
    assert response.status_code == 404
    data = response.json()
    assert "code" in data
    assert data["code"] == "NOT_FOUND"
    assert "detail" in data
    assert "세부항목을 찾을 수 없습니다" in data["detail"]


@pytest.mark.asyncio
async def test_get_core_content_null(client, test_db_session):
    """세부항목 핵심 정보 조회 (core_content가 null인 경우)"""
    subject = Subject(id=1, name="ADsP", description="테스트 과목")
    main_topic = MainTopic(id=1, subject_id=1, name="주요항목1", description="테스트 주요항목")
    sub_topic = SubTopic(
        id=1,
        main_topic_id=1,
        name="세부항목1",
        description="테스트 세부항목",
        core_content=None
    )
    test_db_session.add(subject)
    test_db_session.add(main_topic)
    test_db_session.add(sub_topic)
    await test_db_session.commit()
    
    response = client.get("/api/v1/core-content/1")
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["name"] == "세부항목1"
    assert "core_contents" in data
    assert isinstance(data["core_contents"], list)
    assert len(data["core_contents"]) == 0


@pytest.mark.asyncio
async def test_post_core_content_success(client, test_db_session):
    """핵심 정보 등록 성공"""
    subject = Subject(id=1, name="ADsP", description="테스트 과목")
    main_topic = MainTopic(id=1, subject_id=1, name="주요항목1", description="테스트 주요항목")
    sub_topic = SubTopic(
        id=1,
        main_topic_id=1,
        name="세부항목1",
        description="테스트 세부항목",
        core_content=None
    )
    test_db_session.add(subject)
    test_db_session.add(main_topic)
    test_db_session.add(sub_topic)
    await test_db_session.commit()
    
    response = client.post(
        "/api/v1/main-topics/1/sub-topics/1/core-content",
        json={
            "core_content": "테스트 핵심 정보 내용",
            "source_type": "text"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert "core_contents" in data
    assert isinstance(data["core_contents"], list)
    assert len(data["core_contents"]) == 1
    assert data["core_contents"][0]["core_content"] == "테스트 핵심 정보 내용"
    assert data["core_contents"][0]["source_type"] == "text"
    assert "updated_at" in data


@pytest.mark.asyncio
async def test_post_core_content_multiple(client, test_db_session):
    """핵심 정보 다중 등록 허용"""
    subject = Subject(id=1, name="ADsP", description="테스트 과목")
    main_topic = MainTopic(id=1, subject_id=1, name="주요항목1", description="테스트 주요항목")
    sub_topic = SubTopic(
        id=1,
        main_topic_id=1,
        name="세부항목1",
        description="테스트 세부항목",
        core_content="첫 번째 내용"
    )
    test_db_session.add(subject)
    test_db_session.add(main_topic)
    test_db_session.add(sub_topic)
    await test_db_session.commit()
    
    # 두 번째 핵심 정보 추가
    response = client.post(
        "/api/v1/main-topics/1/sub-topics/1/core-content",
        json={
            "core_content": "두 번째 내용",
            "source_type": "text"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert "core_contents" in data
    assert isinstance(data["core_contents"], list)
    assert len(data["core_contents"]) == 2
    
    # 핵심 정보 내용 확인
    core_content_texts = [item["core_content"] for item in data["core_contents"]]
    assert "두 번째 내용" in core_content_texts
    assert "첫 번째 내용" in core_content_texts
    
    # source_type 확인
    assert all(item["source_type"] == "text" for item in data["core_contents"])


@pytest.mark.asyncio
async def test_post_core_content_invalid_category(client, test_db_session):
    """잘못된 카테고리 (main_topic_id와 sub_topic_id 불일치)"""
    subject = Subject(id=1, name="ADsP", description="테스트 과목")
    main_topic1 = MainTopic(id=1, subject_id=1, name="주요항목1", description="테스트 주요항목")
    main_topic2 = MainTopic(id=2, subject_id=1, name="주요항목2", description="테스트 주요항목2")
    sub_topic = SubTopic(
        id=1,
        main_topic_id=2,  # main_topic_id=2에 속함
        name="세부항목1",
        description="테스트 세부항목",
        core_content=None
    )
    test_db_session.add(subject)
    test_db_session.add(main_topic1)
    test_db_session.add(main_topic2)
    test_db_session.add(sub_topic)
    await test_db_session.commit()
    
    # main_topic_id=1로 요청하지만 sub_topic은 main_topic_id=2에 속함
    response = client.post(
        "/api/v1/main-topics/1/sub-topics/1/core-content",
        json={
            "core_content": "테스트 내용",
            "source_type": "text"
        }
    )
    
    assert response.status_code == 400
    data = response.json()
    assert data["code"] == "INVALID_CATEGORY"
    assert "일치하지 않습니다" in data["detail"]


@pytest.mark.asyncio
async def test_post_core_content_main_topic_not_found(client, test_db_session):
    """존재하지 않는 주요항목"""
    subject = Subject(id=1, name="ADsP", description="테스트 과목")
    main_topic = MainTopic(id=1, subject_id=1, name="주요항목1", description="테스트 주요항목")
    sub_topic = SubTopic(
        id=1,
        main_topic_id=1,
        name="세부항목1",
        description="테스트 세부항목",
        core_content=None
    )
    test_db_session.add(subject)
    test_db_session.add(main_topic)
    test_db_session.add(sub_topic)
    await test_db_session.commit()
    
    response = client.post(
        "/api/v1/main-topics/999/sub-topics/1/core-content",
        json={
            "core_content": "테스트 내용",
            "source_type": "text"
        }
    )
    
    assert response.status_code == 404
    data = response.json()
    assert data["code"] == "NOT_FOUND"
    assert "주요항목을 찾을 수 없습니다" in data["detail"]


@pytest.mark.asyncio
async def test_post_core_content_sub_topic_not_found(client, test_db_session):
    """존재하지 않는 세부항목"""
    subject = Subject(id=1, name="ADsP", description="테스트 과목")
    main_topic = MainTopic(id=1, subject_id=1, name="주요항목1", description="테스트 주요항목")
    test_db_session.add(subject)
    test_db_session.add(main_topic)
    await test_db_session.commit()
    
    response = client.post(
        "/api/v1/main-topics/1/sub-topics/999/core-content",
        json={
            "core_content": "테스트 내용",
            "source_type": "text"
        }
    )
    
    assert response.status_code == 400
    data = response.json()
    assert data["code"] == "INVALID_CATEGORY"
    assert "일치하지 않습니다" in data["detail"]


@pytest.mark.asyncio
async def test_post_core_content_auto_success(client, test_db_session):
    """핵심 정보 자동 분류 성공 (텍스트)"""
    subject = Subject(id=1, name="ADsP", description="테스트 과목")
    main_topic = MainTopic(id=1, subject_id=1, name="R기초와 데이터 마트", description="테스트 주요항목")
    sub_topic1 = SubTopic(
        id=1,
        main_topic_id=1,
        name="R기초",
        description="R 기초 문법",
        core_content=None,
    )
    sub_topic2 = SubTopic(
        id=2,
        main_topic_id=1,
        name="데이터 마트",
        description="데이터 마트 관련",
        core_content=None,
    )
    test_db_session.add(subject)
    test_db_session.add(main_topic)
    test_db_session.add(sub_topic1)
    test_db_session.add(sub_topic2)
    test_db_session.add(CoreContentAutoSetting(min_confidence=0.01))
    await test_db_session.commit()
    
    response = client.post(
        "/api/v1/admin/core-content/auto",
        json={
            "core_content": "R기초에서 벡터와 데이터 프레임을 학습합니다.",
            "source_type": "text",
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["category_path"] is not None
    assert "R기초" in data["category_path"]
    assert data["confidence"] is not None
    assert len(data["candidates"]) >= 1
    assert data["updated_at"] is not None
    
    updated_sub_topic = await test_db_session.get(SubTopic, 1)
    assert updated_sub_topic is not None
    assert updated_sub_topic.core_content is not None
    assert "R기초에서 벡터" in updated_sub_topic.core_content
    
    run_result = await test_db_session.execute(select(CoreContentAutoRun))
    run = run_result.scalar_one()
    assert run.status == "applied"


@pytest.mark.asyncio
async def test_post_core_content_auto_youtube_url(client, test_db_session, monkeypatch):
    """핵심 정보 자동 분류 성공 (YouTube URL)"""
    subject = Subject(id=1, name="ADsP", description="테스트 과목")
    main_topic = MainTopic(id=1, subject_id=1, name="데이터의 이해", description="테스트 주요항목")
    sub_topic = SubTopic(
        id=1,
        main_topic_id=1,
        name="데이터베이스의 정의와 특징",
        description="DB 정의와 특징",
        core_content=None,
    )
    test_db_session.add(subject)
    test_db_session.add(main_topic)
    test_db_session.add(sub_topic)
    test_db_session.add(CoreContentAutoSetting(min_confidence=0.01))
    await test_db_session.commit()
    
    def fake_extract_video_id(url: str) -> str:
        return "test_video_id"
    
    async def fake_extract_transcript(video_id: str) -> str:
        return "데이터베이스의 정의와 특징을 설명합니다."
    
    monkeypatch.setattr(youtube_service, "extract_video_id", fake_extract_video_id)
    monkeypatch.setattr(youtube_service, "extract_transcript", fake_extract_transcript)
    
    response = client.post(
        "/api/v1/admin/core-content/auto",
        json={
            "core_content": "https://youtu.be/test",
            "source_type": "youtube_url",
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["category_path"] is not None
    assert "데이터베이스의 정의와 특징" in data["category_path"]
    assert data["confidence"] is not None
    assert len(data["candidates"]) >= 1
    assert data["updated_at"] is not None


@pytest.mark.asyncio
async def test_post_core_content_auto_invalid_source_type(client, test_db_session):
    """핵심 정보 자동 분류 실패 (잘못된 source_type)"""
    subject = Subject(id=1, name="ADsP", description="테스트 과목")
    main_topic = MainTopic(id=1, subject_id=1, name="데이터의 이해", description="테스트 주요항목")
    sub_topic = SubTopic(
        id=1,
        main_topic_id=1,
        name="데이터와 정보",
        description="테스트 세부항목",
        core_content=None,
    )
    test_db_session.add(subject)
    test_db_session.add(main_topic)
    test_db_session.add(sub_topic)
    await test_db_session.commit()
    
    response = client.post(
        "/api/v1/admin/core-content/auto",
        json={
            "core_content": "데이터와 정보",
            "source_type": "invalid",
        }
    )
    
    assert response.status_code == 400
    data = response.json()
    assert data["code"] == "INVALID_SOURCE_TYPE"
    assert "source_type" in data["detail"]


@pytest.mark.asyncio
async def test_post_core_content_auto_pending_and_review(client, test_db_session):
    """핵심 정보 자동 분류 보류 후 승인/오버라이드"""
    subject = Subject(id=1, name="ADsP", description="테스트 과목")
    main_topic = MainTopic(id=1, subject_id=1, name="데이터의 이해", description="테스트 주요항목")
    sub_topic1 = SubTopic(
        id=1,
        main_topic_id=1,
        name="데이터와 정보",
        description="데이터의 정의",
        core_content=None,
    )
    sub_topic2 = SubTopic(
        id=2,
        main_topic_id=1,
        name="데이터베이스의 정의와 특징",
        description="DB 정의와 특징",
        core_content=None,
    )
    test_db_session.add(subject)
    test_db_session.add(main_topic)
    test_db_session.add(sub_topic1)
    test_db_session.add(sub_topic2)
    test_db_session.add(CoreContentAutoSetting(min_confidence=1.0))
    await test_db_session.commit()
    
    response = client.post(
        "/api/v1/admin/core-content/auto",
        json={
            "core_content": "데이터와 정보의 차이를 설명합니다.",
            "source_type": "text",
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["category_path"] is None
    assert data["updated_at"] is None
    assert len(data["candidates"]) >= 1
    
    pending_response = client.get("/api/v1/admin/core-content/auto/pending")
    assert pending_response.status_code == 200
    pending_data = pending_response.json()
    assert pending_data["total"] == 1
    run_id = pending_data["items"][0]["run_id"]
    
    approve_response = client.post(
        f"/api/v1/admin/core-content/auto/{run_id}/approve",
        json={"sub_topic_id": 2, "reason": "수동 검수 결과"},
    )
    assert approve_response.status_code == 200
    approve_data = approve_response.json()
    assert approve_data["status"] in ("applied", "overridden")
    assert approve_data["final_sub_topic_id"] == 2
    
    updated_sub_topic = await test_db_session.get(SubTopic, 2)
    assert updated_sub_topic.core_content is not None
    
    override_result = await test_db_session.execute(select(CoreContentAutoOverride))
    override = override_result.scalar_one_or_none()
    assert override is not None


@pytest.mark.asyncio
async def test_core_content_auto_settings_update(client, test_db_session):
    """자동 분류 설정 조회 및 업데이트"""
    get_response = client.get("/api/v1/admin/core-content/auto/settings")
    assert get_response.status_code == 200
    data = get_response.json()
    assert "min_confidence" in data
    assert "strategy" in data
    
    update_response = client.put(
        "/api/v1/admin/core-content/auto/settings",
        json={
            "min_confidence": 0.5,
            "strategy": "keyword_only",
            "max_candidates": 2,
        }
    )
    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated["min_confidence"] == 0.5
    assert updated["strategy"] == "keyword_only"
    assert updated["max_candidates"] == 2


@pytest.mark.asyncio
async def test_post_core_content_auto_reject(client, test_db_session):
    """자동 분류 보류 후 거절"""
    subject = Subject(id=1, name="ADsP", description="테스트 과목")
    main_topic = MainTopic(id=1, subject_id=1, name="데이터의 이해", description="테스트 주요항목")
    sub_topic = SubTopic(
        id=1,
        main_topic_id=1,
        name="데이터와 정보",
        description="데이터의 정의",
        core_content=None,
    )
    test_db_session.add(subject)
    test_db_session.add(main_topic)
    test_db_session.add(sub_topic)
    test_db_session.add(CoreContentAutoSetting(min_confidence=1.0))
    await test_db_session.commit()
    
    response = client.post(
        "/api/v1/admin/core-content/auto",
        json={
            "core_content": "데이터와 정보의 차이를 설명합니다.",
            "source_type": "text",
        }
    )
    assert response.status_code == 200
    
    pending_response = client.get("/api/v1/admin/core-content/auto/pending")
    pending_data = pending_response.json()
    run_id = pending_data["items"][0]["run_id"]
    
    reject_response = client.post(
        f"/api/v1/admin/core-content/auto/{run_id}/reject",
        json={"reason": "보류 후 거절"},
    )
    assert reject_response.status_code == 200
    reject_data = reject_response.json()
    assert reject_data["status"] == "rejected"
    
    pending_after = client.get("/api/v1/admin/core-content/auto/pending")
    assert pending_after.json()["total"] == 0
    
    run_result = await test_db_session.execute(select(CoreContentAutoRun))
    run = run_result.scalar_one()
    assert run.status == "rejected"
