#!/bin/bash
# ADsP Quiz Backend 배포 스크립트
# 사용법: ./scripts/deploy/deploy.sh

set -e

PROJECT_DIR="${PROJECT_DIR:-/opt/adsp-quiz-backend}"
ENV_FILE="${ENV_FILE:-${PROJECT_DIR}/env/.env}"

export PROJECT_DIR ENV_FILE

echo "=== ADsP Quiz Backend 배포 스크립트 ==="

echo "📁 [1/4] 배포 준비..."
if [ -f "${PROJECT_DIR}/scripts/deploy/steps/env/prepare-deploy.sh" ]; then
    chmod +x "${PROJECT_DIR}/scripts/deploy/steps/env/prepare-deploy.sh"
    "${PROJECT_DIR}/scripts/deploy/steps/env/prepare-deploy.sh" || exit 1
fi

echo "🚀 [2/4] 애플리케이션 빌드..."
if [ -f "${PROJECT_DIR}/scripts/deploy/steps/app/build-app.sh" ]; then
    chmod +x "${PROJECT_DIR}/scripts/deploy/steps/app/build-app.sh"
    "${PROJECT_DIR}/scripts/deploy/steps/app/build-app.sh" || exit 1
fi

echo "🗄️  [3/5] 데이터베이스 마이그레이션..."
if [ -f "${PROJECT_DIR}/scripts/deploy/steps/app/run-migration.sh" ]; then
    chmod +x "${PROJECT_DIR}/scripts/deploy/steps/app/run-migration.sh"
    "${PROJECT_DIR}/scripts/deploy/steps/app/run-migration.sh" || exit 1
fi

echo "✅ [4/5] 초기 데이터 검증..."
if [ -f "${PROJECT_DIR}/scripts/db/verify-initial-data.sh" ]; then
    chmod +x "${PROJECT_DIR}/scripts/db/verify-initial-data.sh"
    "${PROJECT_DIR}/scripts/db/verify-initial-data.sh" || exit 1
else
    echo "⚠️  초기 데이터 검증 스크립트를 찾을 수 없습니다."
fi

echo "🏥 [5/5] 헬스체크..."
if [ -f "${PROJECT_DIR}/scripts/utils/health-check.sh" ]; then
    chmod +x "${PROJECT_DIR}/scripts/utils/health-check.sh"
    "${PROJECT_DIR}/scripts/utils/health-check.sh" "https://adsp-api.livbee.co.kr/health" 1 5 "$ENV_FILE" || true
fi

echo "=== 배포 완료 ==="
