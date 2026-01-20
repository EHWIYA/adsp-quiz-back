"""Core Content API 통합 테스트"""
import pytest

from app.models.subject import Subject
from app.models.main_topic import MainTopic
from app.models.sub_topic import SubTopic


@pytest.mark.asyncio
async def test_get_core_content(client, test_db_session):
    """세부항목 핵심 정보 조회"""
    subject = Subject(id=1, name="ADsP", description="테스트 과목")
    main_topic = MainTopic(id=1, subject_id=1, name="주요항목1", description="테스트 주요항목")
    sub_topic = SubTopic(
        id=1,
        main_topic_id=1,
        name="세부항목1",
        description="테스트 세부항목",
        core_content="핵심 정보 내용"
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
    assert data["core_content"] == "핵심 정보 내용"
    assert "source_type" in data
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
    assert data["core_content"] is None


@pytest.mark.asyncio
async def test_put_core_content_success(client, test_db_session):
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
    
    response = client.put(
        "/api/v1/main-topics/1/sub-topics/1/core-content",
        json={
            "core_content": "테스트 핵심 정보 내용",
            "source_type": "text"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["core_content"] == "테스트 핵심 정보 내용"
    assert data["source_type"] == "text"
    assert "updated_at" in data


@pytest.mark.asyncio
async def test_put_core_content_already_exists(client, test_db_session):
    """핵심 정보 중복 등록 방지"""
    subject = Subject(id=1, name="ADsP", description="테스트 과목")
    main_topic = MainTopic(id=1, subject_id=1, name="주요항목1", description="테스트 주요항목")
    sub_topic = SubTopic(
        id=1,
        main_topic_id=1,
        name="세부항목1",
        description="테스트 세부항목",
        core_content="이미 등록된 내용"
    )
    test_db_session.add(subject)
    test_db_session.add(main_topic)
    test_db_session.add(sub_topic)
    await test_db_session.commit()
    
    response = client.put(
        "/api/v1/main-topics/1/sub-topics/1/core-content",
        json={
            "core_content": "새로운 내용",
            "source_type": "text"
        }
    )
    
    assert response.status_code == 409
    data = response.json()
    assert data["code"] == "ALREADY_EXISTS"
    assert "이미 등록된 핵심 정보입니다" in data["detail"]


@pytest.mark.asyncio
async def test_put_core_content_invalid_category(client, test_db_session):
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
    response = client.put(
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
async def test_put_core_content_main_topic_not_found(client, test_db_session):
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
    
    response = client.put(
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
async def test_put_core_content_sub_topic_not_found(client, test_db_session):
    """존재하지 않는 세부항목"""
    subject = Subject(id=1, name="ADsP", description="테스트 과목")
    main_topic = MainTopic(id=1, subject_id=1, name="주요항목1", description="테스트 주요항목")
    test_db_session.add(subject)
    test_db_session.add(main_topic)
    await test_db_session.commit()
    
    response = client.put(
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
