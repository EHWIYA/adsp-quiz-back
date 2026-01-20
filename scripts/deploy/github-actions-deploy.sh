#!/bin/bash
# GitHub Actions 배포 스크립트
# 사용법: ./scripts/deploy/github-actions-deploy.sh

set -e

PROJECT_DIR="${PROJECT_DIR:-/opt/adsp-quiz-backend}"
ENV_FILE="${ENV_FILE:-${PROJECT_DIR}/env/.env}"

export PROJECT_DIR ENV_FILE

echo "=== GitHub Actions 배포 시작 ==="
cd "$PROJECT_DIR" || exit 1

echo "📦 [1/4] 환경 준비..."
if [ -f "${PROJECT_DIR}/scripts/deploy/steps/env/prepare-env.sh" ]; then
    chmod +x "${PROJECT_DIR}/scripts/deploy/steps/env/prepare-env.sh"
    "${PROJECT_DIR}/scripts/deploy/steps/env/prepare-env.sh" || exit 1
fi

echo "✅ [2/4] 환경변수 검증..."
if [ -f "${PROJECT_DIR}/scripts/deploy/steps/env/verify-env.sh" ]; then
    chmod +x "${PROJECT_DIR}/scripts/deploy/steps/env/verify-env.sh"
    "${PROJECT_DIR}/scripts/deploy/steps/env/verify-env.sh" || exit 1
fi

echo "🚀 [3/4] 배포 실행..."
if [ -f "${PROJECT_DIR}/scripts/deploy/steps/app/run-deploy.sh" ]; then
    chmod +x "${PROJECT_DIR}/scripts/deploy/steps/app/run-deploy.sh"
    "${PROJECT_DIR}/scripts/deploy/steps/app/run-deploy.sh" || exit 1
fi

echo "🏥 [4/4] 헬스체크..."
if [ -f "${PROJECT_DIR}/scripts/deploy/steps/health-check.sh" ]; then
    chmod +x "${PROJECT_DIR}/scripts/deploy/steps/health-check.sh"
    "${PROJECT_DIR}/scripts/deploy/steps/health-check.sh" || exit 1
fi

echo "=== 배포 완료 ==="
