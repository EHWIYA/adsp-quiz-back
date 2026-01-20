#!/bin/bash
# 원격 서버 배포 스크립트
# 사용법: ./scripts/deploy/ssh/remote-deploy.sh

set -e

PROJECT_DIR="/opt/adsp-quiz-backend"
ENV_FILE="${PROJECT_DIR}/env/.env"

if [ ! -d "$PROJECT_DIR" ]; then
  echo "📦 프로젝트 디렉토리 생성 중..."
  sudo mkdir -p "$PROJECT_DIR"
  sudo chown -R ${USER}:${USER} "$PROJECT_DIR" || true
fi

cd "$PROJECT_DIR" || exit 1

if [ ! -d ".git" ]; then
  echo "📦 Git 저장소 초기화 중..."
  git init || true
  git remote add origin https://github.com/EHWIYA/adsp-quiz-back.git || git remote set-url origin https://github.com/EHWIYA/adsp-quiz-back.git || true
fi

echo "📦 [0/8] Git 코드 동기화 시작..."
git fetch origin || true
git reset --hard origin/main || true
git clean -fd --exclude='data/postgres' || true
echo "✅ 코드 동기화 완료"

export DATABASE_URL="${DATABASE_URL}"
export DB_USER="${DB_USER}"
export DB_PASSWORD="${DB_PASSWORD}"
export GEMINI_API_KEY="${GEMINI_API_KEY:-}"
export GEMINI_MAX_CONCURRENT="${GEMINI_MAX_CONCURRENT:-2}"
export SECRET_KEY="${SECRET_KEY}"
export ALLOWED_ORIGINS="${ALLOWED_ORIGINS}"
export ENV_FILE PROJECT_DIR

if [ -f "${PROJECT_DIR}/scripts/deploy/github-actions-deploy.sh" ]; then
  chmod +x "${PROJECT_DIR}/scripts/deploy/github-actions-deploy.sh"
  "${PROJECT_DIR}/scripts/deploy/github-actions-deploy.sh" || exit 1
else
  echo "❌ GitHub Actions 배포 스크립트를 찾을 수 없습니다."
  echo "현재 디렉토리: $(pwd)"
  echo "스크립트 경로: ${PROJECT_DIR}/scripts/deploy/github-actions-deploy.sh"
  ls -la "${PROJECT_DIR}/scripts/deploy/" 2>/dev/null || echo "scripts/deploy 디렉토리가 존재하지 않습니다."
  exit 1
fi
