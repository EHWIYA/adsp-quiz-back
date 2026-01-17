"""YouTube 서비스 테스트"""
import pytest

from app.services.youtube_service import extract_video_id, generate_hash


def test_extract_video_id_youtube_com():
    """youtube.com URL에서 video_id 추출"""
    url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    assert extract_video_id(url) == "dQw4w9WgXcQ"


def test_extract_video_id_youtu_be():
    """youtu.be URL에서 video_id 추출"""
    url = "https://youtu.be/dQw4w9WgXcQ"
    assert extract_video_id(url) == "dQw4w9WgXcQ"


def test_extract_video_id_with_params():
    """파라미터가 있는 URL에서 video_id 추출"""
    url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=10s"
    assert extract_video_id(url) == "dQw4w9WgXcQ"


def test_extract_video_id_invalid():
    """유효하지 않은 URL 처리"""
    with pytest.raises(ValueError, match="유효하지 않은 YouTube URL"):
        extract_video_id("https://example.com/video")


def test_generate_hash():
    """해시 생성 테스트"""
    text = "test text"
    hash1 = generate_hash(text)
    hash2 = generate_hash(text)
    
    assert hash1 == hash2
    assert len(hash1) == 32
    assert isinstance(hash1, str)


def test_generate_hash_different_texts():
    """다른 텍스트는 다른 해시 생성"""
    hash1 = generate_hash("text1")
    hash2 = generate_hash("text2")
    
    assert hash1 != hash2
