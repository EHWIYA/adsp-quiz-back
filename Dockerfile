# ADsP Quiz Backend Dockerfile
# 중요: migrations 디렉토리가 반드시 포함되어야 합니다!

FROM python:3.11-slim

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 의존성 설치
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Python 의존성 설치
# pyproject.toml과 app 디렉토리를 먼저 복사 (pip install -e . 실행을 위해 필요)
COPY pyproject.toml ./
COPY app/ ./app/
RUN pip install --no-cache-dir -e .

# ⚠️ 중요: migrations 디렉토리 및 Alembic 설정 파일 복사 (필수!)
# 이 부분이 없으면 마이그레이션이 실행되지 않습니다.
COPY migrations/ ./migrations/
COPY alembic.ini ./
COPY migrations/env.py ./migrations/env.py

# 포트 노출
EXPOSE 8001

# 애플리케이션 실행
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
